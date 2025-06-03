"""
DevRev Create Object Tool

Creates new issues or tickets in DevRev.
"""

import json
from fastmcp import Context
from ..utils import make_devrev_request
from ..error_handler import tool_error_handler
from ..endpoints import WORKS_CREATE


@tool_error_handler("create_object")
async def create_object(
    type: str,
    title: str, 
    applies_to_part: str,
    ctx: Context,
    body: str = "",
    owned_by: list[str] | None = None
) -> str:
    """
    Create a new issue or ticket in DevRev.
    
    Args:
        type: The type of object to create ("issue" or "ticket")
        title: The title/summary of the object
        applies_to_part: The part ID this object applies to
        body: The body/description of the object (optional)
        owned_by: List of user IDs who should own this object (optional)
        ctx: FastMCP context
    
    Returns:
        JSON string containing the created object information
    """
    if type not in ["issue", "ticket"]:
        raise ValueError(f"Invalid type '{type}'. Must be 'issue' or 'ticket'")
    
    try:
        await ctx.info(f"Creating new {type}: {title}")
        
        payload = {
            "type": type,
            "title": title,
            "applies_to_part": applies_to_part
        }
        
        if body:
            payload["body"] = body
        if owned_by:
            payload["owned_by"] = owned_by
        
        response = make_devrev_request(WORKS_CREATE, payload)
        
        if response.status_code != 200:
            error_text = response.text
            await ctx.error(f"Failed to create {type}: HTTP {response.status_code} - {error_text}")
            raise ValueError(f"Failed to create {type} (HTTP {response.status_code}): {error_text}")
        
        result_data = response.json()
        await ctx.info(f"Successfully created {type} with ID: {result_data.get('work', {}).get('id', 'unknown')}")
        
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        await ctx.error(f"Failed to create {type}: {str(e)}")
        raise