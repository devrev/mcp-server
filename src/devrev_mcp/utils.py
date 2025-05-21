"""
Copyright (c) 2025 DevRev, Inc.
SPDX-License-Identifier: MIT

This module provides utility functions for making authenticated requests to the DevRev API.
"""

import os
import requests
from typing import Any, Dict

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

def make_internal_devrev_request(endpoint: str, payload: Dict[str, Any]) -> requests.Response:
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
        f"https://api.devrev.ai/internal/{endpoint}",
        headers=headers,
        json=payload
    )
