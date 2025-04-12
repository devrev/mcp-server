"""
Copyright (c) 2025 DevRev, Inc.
SPDX-License-Identifier: MIT

This module provides utility functions for making authenticated requests to the DevRev API.
"""

import os
import requests
from typing import Any, Dict, Tuple, Optional

def make_devrev_request(endpoint: str, payload: Dict[str, Any]) -> requests.Response:
    """
    Make an authenticated request to the DevRev API.
    
    Args:
        endpoint: The API endpoint path (e.g., "works.get" or "search.hybrid")
        payload: The JSON payload to send
    
    Returns:
        requests.Response object
    
    Raises:
        ValueError: If DEVREV_API_KEY environment variable is not set
    """
    api_key = os.environ.get("DEVREV_API_KEY")
    if not api_key:
        raise ValueError("DEVREV_API_KEY environment variable is not set")

    headers = {
        "Authorization": f"{api_key}",
        "Content-Type": "application/json",
    }
    
    return requests.post(
        f"https://api.devrev.ai/{endpoint}",
        headers=headers,
        json=payload
    ) 

def search_part_by_name(part_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Search for a part by name and return its ID if found.
    
    Args:
        part_name: The name of the part to search for
    
    Returns:
        Tuple containing:
            - bool: Success status
            - Optional[str]: Part ID if found, None otherwise
            - Optional[str]: Error message if there was an error, None otherwise
    """
    try:
        search_response = make_devrev_request(
            "search.hybrid",
            {"query": part_name, "namespace": "part"}
        )
        if search_response.status_code != 200:
            return False, None, f"Search for part failed with status {search_response.status_code}: {search_response.text}"
        
        search_results = search_response.json()
        if not search_results.get("results") or len(search_results.get("results")) == 0:
            return False, None, f"No parts found matching '{part_name}'"
        
        part_id = search_results.get("results")[0].get("part").get("id")
        return True, part_id, None
    except Exception as e:
        return False, None, f"Failed to search for part: {str(e)}"

def get_current_user_id() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Get the ID of the current authenticated user.
    
    Returns:
        Tuple containing:
            - bool: Success status
            - Optional[str]: User ID if successful, None otherwise
            - Optional[str]: Error message if there was an error, None otherwise
    """
    try:
        owned_by = make_devrev_request(
            "dev-users.self",
            {}
        )
        if owned_by.status_code != 200:
            return False, None, f"Get user failed with status {owned_by.status_code}: {owned_by.text}"
        
        user_id = owned_by.json().get("dev_user").get("id")
        return True, user_id, None
    except Exception as e:
        return False, None, f"Failed to get current user: {str(e)}"