"""
DevRev Update Object Tool

Updates existing issues or tickets in DevRev.
"""

import json
from fastmcp import Context
from ..utils import make_devrev_request
from ..error_handler import tool_error_handler
from ..endpoints import WORKS_UPDATE


@tool_error_handler("update_object")
async def update_object(
    id: str,
    type: str,
    ctx: Context,
    devrev_cache: dict | None = None,
    title: str | None = None,
    body: str | None = None
) -> str:
    """
    Update an existing issue or ticket in DevRev.
    
    Args:
        id: The ID of the object to update
        type: The type of object ("issue" or "ticket")
        title: New title for the object (optional)
        body: New body/description for the object (optional)
        ctx: FastMCP context
        devrev_cache: Cache dictionary for invalidating cached results
    
    Returns:
        JSON string containing the updated object information
    """
    if type not in ["issue", "ticket"]:
        raise ValueError(f"Invalid type '{type}'. Must be 'issue' or 'ticket'")
    
    if not title and not body:
        raise ValueError("At least one of 'title' or 'body' must be provided for update")
    
    try:
        await ctx.info(f"Updating {type} {id}")
        
        payload = {
            "id": id,
            "type": type
        }
        
        if title:
            payload["title"] = title
        if body:
            payload["body"] = body
        
        response = make_devrev_request(WORKS_UPDATE, payload)
        
        if response.status_code != 200:
            error_text = response.text
            await ctx.error(f"Failed to update {type}: HTTP {response.status_code} - {error_text}")
            raise ValueError(f"Failed to update {type} (HTTP {response.status_code}): {error_text}")
        
        result_data = response.json()
        
        # Update cache if we have this object cached
        if devrev_cache:
            devrev_cache.delete(id)
            await ctx.info(f"Cleared cache for updated object: {id}")
        
        await ctx.info(f"Successfully updated {type}: {id}")
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        await ctx.error(f"Failed to update {type}: {str(e)}")
        raise