"""
DevRev Get Ticket Tool

Provides a tool for fetching DevRev tickets with enriched timeline entries and artifact data.
"""

import json
from fastmcp import Context
from ..error_handler import tool_error_handler
from ..utils import read_resource_content


@tool_error_handler("get_ticket")
async def get_ticket(
    id: str,
    ctx: Context
) -> str:
    """
    Get a DevRev ticket with all associated timeline entries and artifacts.
    
    Args:
        id: The DevRev ticket ID - accepts TKT-12345, ISS-9031, or any work item format
        ctx: FastMCP context
    
    Returns:
        JSON string containing the ticket data with timeline entries and artifacts
    """
    # Input validation
    if not id or not id.strip():
        raise ValueError("ID parameter is required and cannot be empty")
    
    try:
        await ctx.info(f"Fetching work item {id} with timeline entries and artifacts")
        
        # Use different resource depending on ID format
        if id.upper().startswith("TKT-"):
            # Extract numeric part for tickets resource
            numeric_id = id.replace("TKT-", "").replace("tkt-", "")
            resource_uri = f"devrev://tickets/{numeric_id}"
        elif id.upper().startswith("ISS-"):
            # Use works resource for issues
            resource_uri = f"devrev://works/{id}"
        else:
            # Use tickets resource for don:core IDs or numeric IDs
            resource_uri = f"devrev://tickets/{id}"
        
        try:
            ticket_data = await read_resource_content(ctx, resource_uri, parse_json=True)
        except Exception as ticket_error:
            await ctx.error(f"Error reading ticket resource {resource_uri}: {str(ticket_error)}")
            raise ticket_error

        if not ticket_data:
            return f"No ticket found with ID {id}"

        # Handle case where ticket_data is unexpectedly a list
        if isinstance(ticket_data, list):
            await ctx.warning(f"ticket_data is unexpectedly a list, using first item")
            if len(ticket_data) > 0:
                ticket_data = ticket_data[0]
            else:
                return f"No ticket data found for ID {id}"

        # Ensure ticket_data is a dict
        if not isinstance(ticket_data, dict):
            await ctx.error(f"ticket_data is not a dict, type: {type(ticket_data)}, value: {repr(ticket_data)}")
            return f"Invalid ticket data format for ID {id} (type: {type(ticket_data)})"

        # Add navigation links for detailed information (no extra data fetching)
        if id.upper().startswith("TKT-"):
            timeline_id = id.replace("TKT-", "").replace("tkt-", "")
        else:
            timeline_id = id
            
        # Add navigation links for detailed information
        ticket_data["_links"] = {
            "timeline": f"devrev://tickets/{timeline_id}/timeline",
            "artifacts": f"devrev://tickets/{timeline_id}/artifacts",
            "self": resource_uri
        }
        
        # Remove any large nested data that might be in the ticket response
        # Keep only core ticket information
        if "timeline_entries" in ticket_data:
            del ticket_data["timeline_entries"]
        if "artifacts" in ticket_data and isinstance(ticket_data["artifacts"], list) and len(ticket_data["artifacts"]) > 0:
            # Keep just the count of artifacts, not the full data
            artifacts_count = len(ticket_data["artifacts"])
            ticket_data["artifacts"] = f"{artifacts_count} artifacts available (use _links.artifacts to access)"
        
        await ctx.info(f"Returning core ticket data for {id} with navigation links")
        return json.dumps(ticket_data, indent=2)

    except Exception as e:
        await ctx.error(f"Failed to get ticket {id}: {str(e)}")
        raise
