"""
Copyright (c) 2025 DevRev, Inc.
SPDX-License-Identifier: MIT

This module provides utility functions for making authenticated requests to the DevRev API.
"""

import json
import os
import requests
from typing import Any, Dict, List, Union
from fastmcp import Context

class SessionManager:
    """Singleton session manager for connection pooling and lifecycle management."""
    
    _instance: 'SessionManager' = None
    _session: requests.Session = None
    
    def __new__(cls) -> 'SessionManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_session(self) -> requests.Session:
        """Get or create a shared requests session for connection pooling."""
        if self._session is None:
            self._session = requests.Session()
            # Configure session for optimal performance
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=10,
                pool_maxsize=20,
                max_retries=3
            )
            self._session.mount('https://', adapter)
            self._session.mount('http://', adapter)
        return self._session
    
    def close_session(self) -> None:
        """Close the session and clean up resources."""
        if self._session is not None:
            self._session.close()
            self._session = None

# Module-level convenience function
def _get_session() -> requests.Session:
    """Get the shared session instance."""
    return SessionManager().get_session()

def make_devrev_request(endpoint: str, payload: Dict[str, Any]) -> requests.Response:
    """
    Make an authenticated request to the DevRev API.
    
    Args:
        endpoint: The API endpoint path (use constants from endpoints.py)
        payload: The JSON payload to send
    
    Returns:
        requests.Response object
    
    Raises:
        ValueError: If DEVREV_API_KEY environment variable is not set
        requests.RequestException: If the HTTP request fails
    """
    api_key = os.environ.get("DEVREV_API_KEY")
    if not api_key:
        raise ValueError("API authentication not configured")

    headers = {
        "Authorization": f"{api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        session = _get_session()
        response = session.post(
            f"https://api.devrev.ai/{endpoint}",
            headers=headers,
            json=payload,
            timeout=30  # Add timeout for better error handling
        )
        return response
    except requests.Timeout as e:
        from .error_handler import APIError
        raise APIError(endpoint, 408, "Request timeout after 30 seconds") from e
    except requests.ConnectionError as e:
        from .error_handler import APIError
        raise APIError(endpoint, 503, f"Connection failed: {str(e)}") from e
    except requests.HTTPError as e:
        from .error_handler import APIError
        raise APIError(endpoint, getattr(e.response, 'status_code', 500), f"HTTP error: {str(e)}") from e
    except requests.RequestException as e:
        from .error_handler import APIError
        raise APIError(endpoint, 500, f"Request failed: {str(e)}") from e



async def read_resource_content(
    ctx: Context, 
    resource_uri: str, 
    parse_json: bool = True,
    require_content: bool = True
) -> Union[Dict[str, Any], str, None]:
    """
    Read content from a DevRev resource URI with consistent error handling.
    
    This utility handles the common pattern of reading from ctx.read_resource,
    extracting content from ReadResourceContents objects, and optionally parsing JSON.
    
    Args:
        ctx: FastMCP context
        resource_uri: The resource URI to read (e.g., "devrev://works/12345")
        parse_json: If True, parse the content as JSON. If False, return raw string.
        require_content: If True, raise an error if no content is found.
    
    Returns:
        - Dict if parse_json=True and content is valid JSON
        - str if parse_json=False or JSON parsing fails
        - None if require_content=False and no content found
    
    Raises:
        ValueError: If require_content=True and no content is found
        json.JSONDecodeError: If parse_json=True but content is not valid JSON
        Exception: If reading the resource fails
    """
    try:
        await ctx.info(f"Reading resource: {resource_uri}")
        resource_result = await ctx.read_resource(resource_uri)
        
        # Extract content following the established pattern
        content_data = None
        
        if isinstance(resource_result, list) and len(resource_result) > 0:
            # It's a list of ReadResourceContents objects
            for i, content_item in enumerate(resource_result):
                if hasattr(content_item, 'content'):
                    try:
                        content_data = content_item.content
                        if i > 0:
                            await ctx.info(f"Successfully got content from item {i}")
                        break
                    except Exception as e:
                        await ctx.warning(f"Content item {i} could not be accessed: {e}")
                        continue
        elif hasattr(resource_result, 'content'):
            # Single ReadResourceContents object
            content_data = resource_result.content
        elif isinstance(resource_result, str):
            # Direct string content
            content_data = resource_result
        else:
            # Fallback to string conversion
            content_data = str(resource_result)
        
        # Check if we got content
        if not content_data:
            if require_content:
                raise ValueError(f"No content found in resource {resource_uri}")
            else:
                await ctx.warning(f"No content found in resource {resource_uri}")
                return None
        
        # Parse JSON if requested
        if parse_json:
            try:
                parsed_data = json.loads(content_data)
                await ctx.info(f"Successfully parsed JSON from resource {resource_uri}")
                return parsed_data
            except json.JSONDecodeError as e:
                await ctx.error(f"Failed to parse JSON from resource {resource_uri}: {e}")
                if require_content:
                    raise
                else:
                    return content_data
        else:
            return content_data
            
    except Exception as e:
        await ctx.error(f"Failed to read resource {resource_uri}: {str(e)}")
        raise


async def get_link_types(ctx: Context, cache: dict) -> Dict[str, Dict[str, str]]:
    """
    Fetch and cache link types from DevRev API.
    
    Returns:
        Dictionary mapping link type IDs to their forward_name and backward_name
    """
    cache_key = "devrev://link_types"
    cached_value = cache.get(cache_key)
    
    if cached_value is not None:
        return cached_value
    
    from .endpoints import LINK_TYPES_LIST  # Import here to avoid circular imports
    
    try:
        response = make_devrev_request(LINK_TYPES_LIST, {})
        
        if response.status_code != 200:
            await ctx.warning(f"Could not fetch link types: HTTP {response.status_code}")
            return {}
            
        data = response.json()
        link_types = data.get("link_types", [])
        
        # Build lookup dictionary
        link_type_map = {}
        for link_type in link_types:
            link_type_id = link_type.get("id", "")
            forward_name = link_type.get("forward_name", "")
            backward_name = link_type.get("backward_name", "")
            
            if link_type_id:
                link_type_map[link_type_id] = {
                    "forward_name": forward_name,
                    "backward_name": backward_name
                }
        
        cache.set(cache_key, link_type_map)
        await ctx.info(f"Cached {len(link_type_map)} link types")
        return link_type_map
        
    except Exception as e:
        await ctx.warning(f"Error fetching link types: {str(e)}")
        return {}


async def fetch_linked_work_items(
    work_item_id: str, 
    work_item_display_id: str,
    work_item_type: str,
    ctx: Context,
    cache: dict = None
) -> List[Dict[str, Any]]:
    """
    Fetch and process linked work items for any DevRev work item.
    
    This utility extracts the linked work items logic from the ticket resource
    to make it reusable across different resource types (tickets, issues, etc.).
    
    Args:
        work_item_id: The full don:core ID of the work item (e.g., "don:core:dvrv-us-1:devo/123:ticket/456")
        work_item_display_id: The display ID of the work item (e.g., "TKT-12345", "ISS-9031")  
        work_item_type: The type of work item ("ticket", "issue", etc.)
        ctx: FastMCP context for logging
        cache: Cache dictionary for storing link types
    
    Returns:
        List of linked work items with navigation links and metadata
    """
    from .endpoints import LINKS_LIST  # Import here to avoid circular imports
    
    # Get link types for better relationship descriptions
    link_types_map = {}
    if cache is not None:
        link_types_map = await get_link_types(ctx, cache)
    
    try:
        links_response = make_devrev_request(
            LINKS_LIST,
            {"object": work_item_id}
        )
        
        if links_response.status_code != 200:
            await ctx.warning(f"Could not fetch links for {work_item_type} {work_item_display_id}")
            return []
            
        links_data = links_response.json()
        links = links_data.get("links", [])
        
        # Process links to extract linked work items
        linked_work_items = []
        current_work_item_id = work_item_id  # The current work item's don:core ID
        
        for link in links:
            # Each link has source, target, link_type, etc.
            target = link.get("target", {})
            source = link.get("source", {})
            link_type = link.get("link_type", "unknown")
            
            # Process both target and source, but exclude the current work item itself
            for linked_item, relationship_direction in [(target, "outbound"), (source, "inbound")]:
                if linked_item and linked_item.get("id") and linked_item.get("id") != current_work_item_id:
                    linked_item_id = linked_item.get("id", "")
                    linked_item_type = linked_item.get("type", "unknown")
                    linked_item_display_id = linked_item.get("display_id", "")
                    linked_item_title = linked_item.get("title", "")
                    
                    # Get proper relationship description using link types
                    relationship_description = ""
                    link_type_info = link_types_map.get(link_type, {})
                    
                    if relationship_direction == "outbound":
                        # Current item -> linked item (use forward_name)
                        forward_name = link_type_info.get("forward_name", link_type)
                        relationship_description = f"{work_item_display_id} {forward_name} {linked_item_display_id}"
                    else:
                        # linked item -> Current item (use backward_name)
                        backward_name = link_type_info.get("backward_name", link_type)
                        relationship_description = f"{linked_item_display_id} {backward_name} {work_item_display_id}"
                    
                    processed_item = {
                        "id": linked_item_id,
                        "type": linked_item_type,
                        "display_id": linked_item_display_id,
                        "title": linked_item_title,
                        "link_type": link_type,
                        "relationship_direction": relationship_direction,
                        "relationship_description": relationship_description,
                        "stage": linked_item.get("stage", {}).get("name", "unknown"),
                        "priority": linked_item.get("priority", "unknown"),
                        "owned_by": linked_item.get("owned_by", []),
                        "links": {}
                    }
                    
                    # Add external reference if available (e.g., Jira link)
                    sync_metadata = linked_item.get("sync_metadata", {})
                    if sync_metadata.get("external_reference"):
                        processed_item["external_reference"] = sync_metadata["external_reference"]
                        processed_item["origin_system"] = sync_metadata.get("origin_system", "unknown")
                    
                    # Add appropriate navigation links based on linked work item type
                    if linked_item_display_id:
                        processed_item["links"]["work_item"] = f"devrev://works/{linked_item_display_id}"
                        
                        if linked_item_type == "ticket" and linked_item_display_id.startswith("TKT-"):
                            ticket_num = linked_item_display_id.replace("TKT-", "")
                            processed_item["links"].update({
                                "ticket": f"devrev://tickets/{ticket_num}",
                                "timeline": f"devrev://tickets/{ticket_num}/timeline",
                                "artifacts": f"devrev://tickets/{ticket_num}/artifacts"
                            })
                        elif linked_item_type == "issue" and linked_item_display_id.startswith("ISS-"):
                            issue_num = linked_item_display_id.replace("ISS-", "")
                            processed_item["links"].update({
                                "issue": f"devrev://issues/{issue_num}",
                                "timeline": f"devrev://issues/{issue_num}/timeline",
                                "artifacts": f"devrev://issues/{issue_num}/artifacts"
                            })
                    
                    # Check if we already have this work item (avoid duplicates)
                    existing_item = next((item for item in linked_work_items if item["id"] == linked_item_id), None)
                    if not existing_item:
                        linked_work_items.append(processed_item)
        
        await ctx.info(f"Added {len(linked_work_items)} linked work items to {work_item_type} {work_item_display_id}")
        return linked_work_items
        
    except Exception as e:
        await ctx.warning(f"Error fetching links for {work_item_type} {work_item_display_id}: {str(e)}")
        return []
