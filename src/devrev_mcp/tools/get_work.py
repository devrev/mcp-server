"""
DevRev Get Work Tool

Provides a tool for fetching any DevRev work item (tickets, issues, etc.) by ID.
"""

import json
from fastmcp import Context
from ..utils import make_devrev_request
from ..endpoints import WORKS_GET
from ..error_handler import tool_error_handler


@tool_error_handler("get_work")
async def get_work(id: str, ctx: Context) -> str:
    """
    Get a DevRev work item (ticket, issue, etc.) by ID.
    
    Args:
        id: The DevRev work ID - accepts TKT-12345, ISS-9031, or any work item format
        ctx: FastMCP context
    
    Returns:
        JSON string containing the work item data
    """
    try:
        await ctx.info(f"Fetching work item {id}")
        
        # Make API request to get work item details using works.get
        payload = {
            "id": id
        }
        
        response = make_devrev_request(WORKS_GET, payload)
        
        if response.status_code != 200:
            await ctx.error(f"DevRev API returned status {response.status_code}")
            return json.dumps({
                "error": f"Failed to fetch work item {id}",
                "status_code": response.status_code,
                "message": response.text
            })
        
        data = response.json()
        work_item = data.get("work")
        
        if not work_item:
            return json.dumps({
                "error": f"Work item {id} not found",
                "message": "No work item found with the provided ID"
            })
        
        # Return the work item data directly
        return json.dumps(work_item, indent=2, default=str)
            
    except Exception as e:
        await ctx.error(f"Failed to get work item {id}: {str(e)}")
        return f"Failed to get work item {id}: {str(e)}"