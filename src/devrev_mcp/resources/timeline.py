"""
DevRev Timeline Resource Handler

Provides enriched timeline access for DevRev tickets with conversation flow and visibility information.
"""

import json
from fastmcp import Context
from ..utils import make_devrev_request
from ..types import VisibilityInfo, format_visibility_summary
from ..error_handler import resource_error_handler
from ..endpoints import WORKS_GET, TIMELINE_ENTRIES_LIST
@resource_error_handler("timeline")
async def timeline(ticket_id: str, ctx: Context, devrev_cache: dict) -> str:
    """
    Access enriched timeline for a ticket with structured conversation format.
    
    Args:
        ticket_id: The DevRev ticket ID (e.g., 12345 for TKT-12345)
        ctx: FastMCP context
    
    Returns:
        JSON string containing enriched timeline with customer context and conversation flow
    """
    try:
        # ticket_id is already normalized by server.py pattern matching
        cache_key = f"ticket_timeline:{ticket_id}"
        
        # Check cache first
        cached_value = devrev_cache.get(cache_key)
        if cached_value is not None:
            await ctx.info(f"Retrieved timeline for {ticket_id} from cache")
            return cached_value
        
        await ctx.info(f"Fetching timeline for {ticket_id} from DevRev API")
        
        # Get ticket details for customer and workspace info
        ticket_response = make_devrev_request(WORKS_GET, {"id": ticket_id})
        if ticket_response.status_code != 200:
            raise ValueError(f"Failed to fetch ticket {ticket_id}")
        
        ticket_data = ticket_response.json()
        work = ticket_data.get("work", {})
        
        # Get timeline entries with pagination
        all_entries = []
        cursor = None
        page_count = 0
        max_pages = 50  # Safety limit to prevent infinite loops
        
        while page_count < max_pages:
            request_payload = {
                "object": ticket_id,
                "limit": 50  # Use DevRev's default limit
            }
            if cursor:
                request_payload["cursor"] = cursor
                request_payload["mode"] = "after"  # Get entries after this cursor
            
            timeline_response = make_devrev_request(
                TIMELINE_ENTRIES_LIST,
                request_payload
            )
            
            if timeline_response.status_code != 200:
                raise ValueError(f"Failed to fetch timeline for {ticket_id}")
            
            timeline_data = timeline_response.json()
            page_entries = timeline_data.get("timeline_entries", [])
            all_entries.extend(page_entries)
            
            # Check for next page using DevRev's cursor system
            cursor = timeline_data.get("next_cursor")
            page_count += 1
            
            await ctx.info(f"DEBUG: Fetched page {page_count} with {len(page_entries)} entries, total so far: {len(all_entries)}")
            
            # Break if no more pages or no entries in this page
            if not cursor or len(page_entries) == 0:
                break
        
        await ctx.info(f"DEBUG: Found {len(all_entries)} timeline entries for {ticket_id}")
        
        # Extract customer information
        customer_info = {}
        created_by = work.get("created_by", {})
        if created_by:
            customer_info = {
                "name": created_by.get("display_name", "Unknown"),
                "email": created_by.get("email", ""),
                "type": "customer" if created_by.get("type") == "user" else "system"
            }
        
        # Build enriched schema
        result = {
            "summary": {
                "ticket_id": ticket_id,
                "customer": customer_info.get("email", customer_info.get("name", "Unknown")),
                "workspace": work.get("owned_by", [{}])[0].get("display_name", "Unknown Workspace") if work.get("owned_by") else "Unknown Workspace",
                "subject": work.get("title", "No title"),
                "current_stage": work.get("stage", {}).get("name", "unknown"),
                "created_date": work.get("created_date"),
                "total_artifacts": 0
            },
            "conversation_thread": [],
            "key_events": [],
            "all_artifacts": []
        }
        
        # Process timeline entries into conversation and events
        conversation_seq = 1
        artifacts_found = {}
        
        for entry in all_entries:
            entry_type = entry.get("type", "")
            timestamp = entry.get("created_date", "")
            
            # Extract visibility information
            visibility_raw = entry.get("visibility")
            visibility_info = VisibilityInfo.from_visibility(visibility_raw)
            
            # Handle conversation entries (comments)
            if entry_type == "timeline_comment":
                body = entry.get("body", "")
                author = entry.get("created_by", {})
                
                # Determine speaker type
                speaker_type = "support"
                if author.get("email") == customer_info.get("email"):
                    speaker_type = "customer"
                elif "system" in author.get("display_name", "").lower():
                    speaker_type = "system"
                
                conversation_entry = {
                    "seq": conversation_seq,
                    "timestamp": timestamp,
                    "event_type": entry_type,
                    "speaker": {
                        "name": author.get("display_name", author.get("email", "Unknown")),
                        "type": speaker_type
                    },
                    "message": body,
                    "artifacts": [],
                    "visibility_info": visibility_info.to_dict()
                }
                
                # Add artifacts if present
                if entry.get("artifacts"):
                    for artifact in entry["artifacts"]:
                        artifact_id = artifact.get("id")
                        artifact_info = {
                            "id": artifact_id,
                            "display_id": artifact.get("display_id"),
                            "type": artifact.get("file", {}).get("type", "unknown"),
                            "attached_to_message": conversation_seq,
                            "resource_uri": f"devrev://artifacts/{artifact_id}"
                        }
                        conversation_entry["artifacts"].append(artifact_info)
                        artifacts_found[artifact_id] = artifact_info
                
                # Add timeline entry navigation link
                entry_id = entry.get("id", "").split("/")[-1] if entry.get("id") else ""
                if entry_id:
                    conversation_entry["timeline_entry_uri"] = f"devrev://tickets/{ticket_id}/timeline/{entry_id}"
                
                result["conversation_thread"].append(conversation_entry)
                conversation_seq += 1
                
                # Update last message timestamps
                if speaker_type == "customer":
                    result["summary"]["last_customer_message"] = timestamp
                elif speaker_type == "support":
                    result["summary"]["last_support_response"] = timestamp
            
            # Handle key events
            elif entry_type in ["work_created", "stage_updated", "part_suggested", "work_updated"]:
                event_info = {
                    "type": entry_type.replace("work_", "").replace("_", " "),
                    "event_type": entry_type,
                    "timestamp": timestamp,
                    "visibility_info": visibility_info.to_dict()
                }
                
                # Add context for stage updates
                if entry_type == "stage_updated" and entry.get("stage_updated"):
                    stage_info = entry["stage_updated"]
                    event_info["from_stage"] = stage_info.get("old_stage", {}).get("name")
                    event_info["to_stage"] = stage_info.get("new_stage", {}).get("name")
                
                # Add author information if available
                author = entry.get("created_by", {})
                if author:
                    event_info["actor"] = {
                        "name": author.get("display_name", author.get("email", "System")),
                        "type": "customer" if author.get("email") == customer_info.get("email") else "support"
                    }
                
                result["key_events"].append(event_info)
            
            # Handle all other event types to preserve information
            else:
                # Skip entries without meaningful content
                if not entry_type or entry_type in ["", "unknown"]:
                    continue
                
                # Determine if this is likely a conversation-like entry
                body = entry.get("body", "").strip()
                author = entry.get("created_by", {})
                
                if body:  # Has content, treat as conversation
                    speaker_type = "support"
                    if author.get("email") == customer_info.get("email"):
                        speaker_type = "customer"
                    elif "system" in author.get("display_name", "").lower():
                        speaker_type = "system"
                    
                    conversation_entry = {
                        "seq": conversation_seq,
                        "timestamp": timestamp,
                        "event_type": entry_type,
                        "speaker": {
                            "name": author.get("display_name", author.get("email", "Unknown")),
                            "type": speaker_type
                        },
                        "message": body,
                        "artifacts": [],
                        "visibility_info": visibility_info.to_dict()
                    }
                    
                    # Add timeline entry navigation link
                    entry_id = entry.get("id", "").split("/")[-1] if entry.get("id") else ""
                    if entry_id:
                        conversation_entry["timeline_entry_uri"] = f"devrev://tickets/{ticket_id}/timeline/{entry_id}"
                    
                    result["conversation_thread"].append(conversation_entry)
                    conversation_seq += 1
                    
                    # Update last message timestamps
                    if speaker_type == "customer":
                        result["summary"]["last_customer_message"] = timestamp
                    elif speaker_type == "support":
                        result["summary"]["last_support_response"] = timestamp
                        
                else:  # No content, treat as event
                    event_info = {
                        "type": entry_type.replace("_", " "),
                        "event_type": entry_type,
                        "timestamp": timestamp,
                        "visibility_info": visibility_info.to_dict()
                    }
                    
                    # Add author information if available
                    if author:
                        event_info["actor"] = {
                            "name": author.get("display_name", author.get("email", "System")),
                            "type": "customer" if author.get("email") == customer_info.get("email") else "support"
                        }
                    
                    result["key_events"].append(event_info)
        
        # Set artifact count and list
        result["all_artifacts"] = list(artifacts_found.values())
        result["summary"]["total_artifacts"] = len(artifacts_found)
        
        # Add visibility summary to the result
        all_entries_with_visibility = result["conversation_thread"] + result["key_events"]
        result["visibility_summary"] = format_visibility_summary(all_entries_with_visibility)
        
        # Add navigation links
        result["links"] = {
            "ticket": f"devrev://tickets/{ticket_id}"
        }
        
        if result["all_artifacts"]:
            result["links"]["artifacts"] = f"devrev://tickets/{ticket_id}/artifacts"
        
        # Cache the enriched result
        cache_value = json.dumps(result, indent=2)
        devrev_cache.set(cache_key, cache_value)
        await ctx.info(f"Successfully retrieved and cached timeline: {ticket_id}")
        
        return cache_value
        
    except Exception as e:
        await ctx.error(f"Failed to get timeline for ticket {ticket_id}: {str(e)}")
        raise ValueError(f"Timeline for ticket {ticket_id} not found: {str(e)}") 