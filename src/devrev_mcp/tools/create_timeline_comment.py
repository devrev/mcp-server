"""
DevRev Create Timeline Comment Tool

Provides a tool for creating internal timeline comments on DevRev tickets and issues.
"""

import json
from fastmcp import Context
from ..error_handler import tool_error_handler
from ..endpoints import TIMELINE_ENTRIES_CREATE
from ..utils import make_devrev_request, read_resource_content


@tool_error_handler("create_timeline_comment")
async def create_timeline_comment(
    work_id: str,
    body: str,
    ctx: Context
) -> str:
    """
    Create an internal timeline comment on a DevRev ticket or issue.
    
    Args:
        work_id: The DevRev work item ID (e.g., "12345", "TKT-12345", "ISS-9465")
        body: The comment text to add to the timeline
        ctx: FastMCP context
    
    Returns:
        JSON string containing the created timeline entry data
    """
    try:
        await ctx.info(f"Creating timeline comment on work item {work_id}")
        
        resource_uri = f"devrev://works/{work_id}"
        await ctx.info(f"Constructed resource URI: {resource_uri}")
        
        try:
            work_item = await read_resource_content(ctx, resource_uri, parse_json=True)
            await ctx.info(f"Successfully retrieved work item. Keys: {list(work_item.keys()) if work_item else 'None'}")
            await ctx.info(f"Work item type: {type(work_item)}")
            if work_item:
                await ctx.info(f"Work item sample: {json.dumps(dict(list(work_item.items())[:5]), indent=2)}")
        except Exception as e:
            await ctx.error(f"Failed to read resource content for {resource_uri}: {str(e)}")
            # Try alternative formats
            alternative_uris = [
                f"devrev://tickets/{work_id}",
                f"devrev://issues/{work_id}",
                f"devrev://works/{work_id.replace('TKT-', '').replace('ISS-', '')}"
            ]
            for alt_uri in alternative_uris:
                try:
                    await ctx.info(f"Trying alternative URI: {alt_uri}")
                    work_item = await read_resource_content(ctx, alt_uri, parse_json=True)
                    await ctx.info(f"Success with alternative URI: {alt_uri}")
                    break
                except Exception as alt_e:
                    await ctx.info(f"Alternative URI {alt_uri} failed: {str(alt_e)}")
            else:
                raise e
        
        # Extract the object ID from the work item - this should be the full don:core ID
        object_id = work_item.get("id")
        await ctx.info(f"Raw object_id extracted: {object_id}")
        await ctx.info(f"Object ID type: {type(object_id)}")
        
        if not object_id:
            await ctx.error(f"Work item: {work_item}")
            raise ValueError(f"Could not extract object ID from work item {work_id}\n{work_item}")


        
        await ctx.info(f"Using object ID: {object_id}")
        
        # Prepare the payload for timeline comment creation using the full object ID
        payload = {
            "body": body,
            "body_type": "text",
            "object": object_id,
            "type": "timeline_comment",
            "collections": ["discussions"],
            "visibility": "internal"
        }
        
        await ctx.info(f"Creating comment with payload: {json.dumps(payload, indent=2)}")
        
        # Make the API request
        response = make_devrev_request(TIMELINE_ENTRIES_CREATE, payload)
        
        if response.status_code == 200 or response.status_code == 201:
            result_data = response.json()
            await ctx.info(f"Successfully created timeline comment on work item {work_id}")
            return json.dumps(result_data, indent=2)
        else:
            error_msg = f"Failed to create timeline comment: HTTP {response.status_code}"
            if response.text:
                error_msg += f" - {response.text}"
            await ctx.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        await ctx.error(f"Failed to create timeline comment on work item {work_id}: {str(e)}")
        raise