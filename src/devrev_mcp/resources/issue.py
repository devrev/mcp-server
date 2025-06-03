"""
DevRev Issue Resource Handler

Provides specialized resource access for DevRev issues with enriched timeline and artifact data.
"""

import json
from fastmcp import Context
from ..utils import make_devrev_request, fetch_linked_work_items
from ..error_handler import resource_error_handler
from ..endpoints import WORKS_GET, TIMELINE_ENTRIES_LIST


@resource_error_handler("issue")
async def issue(issue_number: str, ctx: Context, devrev_cache: dict) -> str:
    """
    Access DevRev issue details with enriched timeline entries and artifact data.
    
    Args:
        issue_number: The numeric DevRev issue number (e.g., "9031")
        ctx: FastMCP context
        devrev_cache: Cache dictionary for storing results
    
    Returns:
        JSON string containing the issue data with timeline entries and artifacts
    """
    # Use the display ID format that the API expects
    issue_id = f"ISS-{issue_number}"
    cache_key = f"devrev://issues/{issue_number}"
    
    # Check cache first
    cached_value = devrev_cache.get(cache_key)
    if cached_value is not None:
        await ctx.info(f"Retrieved issue {issue_number} from cache")
        return cached_value
    
    await ctx.info(f"Fetching issue {issue_id} from DevRev API")
    
    # Get issue details using the display ID
    response = make_devrev_request(WORKS_GET, {"id": issue_id})
    
    if response.status_code != 200:
        error_text = response.text
        await ctx.error(f"Failed to fetch issue {issue_id}: HTTP {response.status_code} - {error_text}")
        raise ValueError(f"Failed to fetch issue {issue_id} (HTTP {response.status_code}): {error_text}")
    
    result = response.json()
    
    # Extract the work object from the API response
    if isinstance(result, dict) and "work" in result:
        result = result["work"]
    
    # Get timeline entries for the issue
    try:
        timeline_response = make_devrev_request(
            TIMELINE_ENTRIES_LIST,
            {"object": issue_id}
        )
        
        if timeline_response.status_code == 200:
            timeline_data = timeline_response.json()
            timeline_entries = timeline_data.get("timeline_entries", [])
            result["timeline_entries"] = timeline_entries
            await ctx.info(f"Added {len(timeline_entries)} timeline entries to issue {issue_id}")
            
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
                                    "issue": f"devrev://issues/{issue_number}"
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
                                        "issue": f"devrev://issues/{issue_number}"
                                    }
                                })
            
            result["artifacts"] = artifacts
            await ctx.info(f"Extracted {len(artifacts)} artifacts from timeline entries for issue {issue_number}")
            
        else:
            await ctx.warning(f"Could not fetch timeline entries for issue {issue_number}")
            result["timeline_entries"] = []
            result["artifacts"] = []
    except Exception as e:
        await ctx.warning(f"Error fetching timeline entries for issue {issue_number}: {str(e)}")
        result["timeline_entries"] = []
        result["artifacts"] = []
    
    # Get linked work items using the reusable utility function
    work_item_don_id = result.get("id", issue_id)  # Use the full don:core ID from the API response
    linked_work_items = await fetch_linked_work_items(
        work_item_id=work_item_don_id,
        work_item_display_id=issue_id,
        work_item_type="issue",
        ctx=ctx,
        cache=devrev_cache
    )

    # Add navigation links
    result["links"] = {
        "timeline": f"devrev://issues/{issue_number}/timeline",
        "artifacts": f"devrev://issues/{issue_number}/artifacts",
        "works": linked_work_items
    }
    
    # Cache the enriched result
    cache_value = json.dumps(result, indent=2, default=str)
    devrev_cache.set(cache_key, cache_value)
    await ctx.info(f"Successfully retrieved and cached issue: {issue_number}")
    
    return cache_value