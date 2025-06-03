"""
DevRev Ticket Resource Handler

Provides specialized resource access for DevRev tickets with enriched timeline and artifact data.
"""

import json
from fastmcp import Context
from ..utils import make_devrev_request, fetch_linked_work_items
from ..error_handler import resource_error_handler
from ..endpoints import WORKS_GET, TIMELINE_ENTRIES_LIST


@resource_error_handler("ticket")
async def ticket(ticket_number: str, ctx: Context, devrev_cache: dict) -> str:
    """
    Access DevRev ticket details with enriched timeline entries and artifact data.
    
    Args:
        ticket_number: The numeric DevRev ticket ID (e.g., "12345")
        ctx: FastMCP context
        devrev_cache: Cache dictionary for storing results
    
    Returns:
        JSON string containing the ticket data with timeline entries and artifacts
    """
    # Use the display ID format that the API expects
    ticket_id = f"TKT-{ticket_number}"
    cache_key = f"devrev://tickets/{ticket_number}"
    
    # Check cache first
    cached_value = devrev_cache.get(cache_key)
    if cached_value is not None:
        await ctx.info(f"Retrieved ticket {ticket_number} from cache")
        return cached_value
    
    await ctx.info(f"Fetching ticket {ticket_id} from DevRev API")
    
    # Get ticket details using the display ID
    response = make_devrev_request(WORKS_GET, {"id": ticket_id})
    
    if response.status_code != 200:
        error_text = response.text
        await ctx.error(f"Failed to fetch ticket {ticket_id}: HTTP {response.status_code} - {error_text}")
        raise ValueError(f"Failed to fetch ticket {ticket_id} (HTTP {response.status_code}): {error_text}")
    
    result = response.json()
    
    # Extract the work object from the API response
    if isinstance(result, dict) and "work" in result:
        result = result["work"]
    
    # Get timeline entries for the ticket
    try:
        timeline_response = make_devrev_request(
            TIMELINE_ENTRIES_LIST,
            {"object": ticket_id}
        )
        
        if timeline_response.status_code == 200:
            timeline_data = timeline_response.json()
            timeline_entries = timeline_data.get("timeline_entries", [])
            result["timeline_entries"] = timeline_entries
            await ctx.info(f"Added {len(timeline_entries)} timeline entries to ticket {ticket_id}")
            
            # Extract artifact data directly from timeline entries (no additional API calls needed)
            artifacts = []
            seen_artifact_ids = set()  # Avoid duplicates across timeline entries
            
            for entry in timeline_entries:
                if "artifacts" in entry:
                    for artifact in entry["artifacts"]:
                        # Timeline entries contain full artifact objects, not just IDs
                        if isinstance(artifact, dict):
                            artifact_id = artifact.get("id", "")
                            if artifact_id and artifact_id not in seen_artifact_ids:
                                seen_artifact_ids.add(artifact_id)
                                
                                # Add navigation link for downloading
                                artifact_id_clean = artifact_id.split("/")[-1] if "/" in artifact_id else artifact_id
                                artifact["links"] = {
                                    "download": f"devrev://artifacts/{artifact_id_clean}/download",
                                    "ticket": f"devrev://tickets/{ticket_number}"
                                }
                                artifacts.append(artifact)
                        elif isinstance(artifact, str):
                            # Fallback: if it's just an ID string, create minimal artifact object
                            if artifact not in seen_artifact_ids:
                                seen_artifact_ids.add(artifact)
                                artifact_id_clean = artifact.split("/")[-1] if "/" in artifact else artifact
                                artifacts.append({
                                    "id": artifact,
                                    "links": {
                                        "download": f"devrev://artifacts/{artifact_id_clean}/download",
                                        "ticket": f"devrev://tickets/{ticket_number}"
                                    }
                                })
            
            result["artifacts"] = artifacts
            await ctx.info(f"Extracted {len(artifacts)} artifacts from timeline entries for ticket {ticket_id}")
            
        else:
            await ctx.warning(f"Could not fetch timeline entries for ticket {ticket_id}")
            result["timeline_entries"] = []
            result["artifacts"] = []
    except Exception as e:
        await ctx.warning(f"Error fetching timeline entries for ticket {ticket_id}: {str(e)}")
        result["timeline_entries"] = []
        result["artifacts"] = []
    
    # Get linked work items using the reusable utility function
    work_item_don_id = result.get("id", ticket_id)  # Use the full don:core ID from the API response
    linked_work_items = await fetch_linked_work_items(
        work_item_id=work_item_don_id,
        work_item_display_id=ticket_id,
        work_item_type="ticket",
        ctx=ctx,
        cache=devrev_cache
    )

    # Add navigation links
    result["links"] = {
        "timeline": f"devrev://tickets/{ticket_number}/timeline",
        "artifacts": f"devrev://tickets/{ticket_number}/artifacts",
        "works": linked_work_items
    }
    
    # Cache the enriched result
    cache_value = json.dumps(result, indent=2, default=str)
    devrev_cache.set(cache_key, cache_value)
    await ctx.info(f"Successfully retrieved and cached ticket: {ticket_number}")
    
    return cache_value