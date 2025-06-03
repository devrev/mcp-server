"""
Copyright (c) 2025 DevRev, Inc.
SPDX-License-Identifier: MIT

DevRev Work Item Resource

Provides a unified resource for accessing work items (tickets, issues, etc.)
via the devrev://work/{work_id} URI format.
"""

import json
from fastmcp import Context
from ..utils import make_devrev_request
from ..endpoints import WORKS_GET
from ..error_handler import resource_error_handler


@resource_error_handler("works")
async def works(work_id: str, ctx: Context, cache=None) -> str:
    """
    Access DevRev work item details using unified work ID format.
    
    Args:
        work_id: The DevRev work ID (e.g., TKT-12345, ISS-9031, or numeric ID)
        ctx: FastMCP context
        cache: Optional cache instance
    
    Returns:
        JSON string containing the work item data with navigation links
    """
    try:
        await ctx.info(f"Fetching work item {work_id}")
        
        # Check cache first if available
        cache_key = f"work_{work_id}"
        if cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                await ctx.info(f"Using cached data for work item {work_id}")
                return cached_result
        
        # Normalize work_id to the format expected by the API
        normalized_work_id = work_id
        
        # The DevRev works.get API accepts both display IDs (TKT-12345, ISS-9031) 
        # and full don:core IDs, so we can pass them directly
        # No transformation needed - the API handles both formats
        
        # Make API request to get work item details using works.get
        payload = {
            "id": normalized_work_id
        }
        
        response = make_devrev_request(WORKS_GET, payload)
        
        if response.status_code != 200:
            await ctx.error(f"DevRev API returned status {response.status_code}")
            return json.dumps({
                "error": f"Failed to fetch work item {work_id}",
                "status_code": response.status_code,
                "message": response.text
            })
        
        data = response.json()
        work_item = data.get("work")
        
        if not work_item:
            return json.dumps({
                "error": f"Work item {work_id} not found",
                "message": "No work item found with the provided ID"
            })
        work_type = work_item.get("type", "unknown")
        
        # Enhance the work item data with navigation links
        enhanced_work = {
            **work_item,
            "links": _build_navigation_links(work_item),
            "metadata": {
                "resource_type": "work",
                "work_type": work_type,
                "fetched_at": data.get("next_cursor", ""),
                "api_version": "v1"
            }
        }
        
        result = json.dumps(enhanced_work, indent=2, default=str)
        
        # Cache the result if cache is available
        if cache:
            cache.set(cache_key, result)  # Cache result
            
        return result
        
    except Exception as e:
        await ctx.error(f"Failed to fetch work item {work_id}: {str(e)}")
        return json.dumps({
            "error": f"Failed to fetch work item {work_id}",
            "message": str(e)
        })


def _build_navigation_links(work_item: dict) -> dict:
    """
    Build navigation links for a work item based on its type and ID.
    
    Args:
        work_item: The work item data from DevRev API
    
    Returns:
        Dictionary of navigation links
    """
    display_id = work_item.get("display_id", "")
    work_type = work_item.get("type", "unknown")
    
    links = {
        "self": f"devrev://work/{display_id}",
    }
    
    # Add type-specific links
    if work_type == "ticket" and display_id.startswith("TKT-"):
        # Extract numeric ID for ticket-specific resources
        numeric_id = display_id.replace("TKT-", "")
        links.update({
            "ticket": f"devrev://tickets/{numeric_id}",
            "timeline": f"devrev://tickets/{numeric_id}/timeline",
            "artifacts": f"devrev://tickets/{numeric_id}/artifacts"
        })
    
    return links