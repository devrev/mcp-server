"""
Copyright (c) 2025 DevRev, Inc.
SPDX-License-Identifier: MIT

This module provides search functionality for DevRev objects.
"""

import json
from typing import Dict, Any, List
from fastmcp import Context

from ..utils import make_devrev_request
from ..error_handler import tool_error_handler
from ..endpoints import SEARCH_HYBRID


@tool_error_handler("search")
async def search(query: str, namespace: str, ctx: Context) -> str:
    """
    Search DevRev using the provided query and return parsed, useful information.
    
    Args:
        query: The search query string
        namespace: The namespace to search in (article, issue, ticket, part, dev_user)
        ctx: FastMCP context for logging
    
    Returns:
        JSON string containing parsed search results with key information
    """
    if namespace not in ["article", "issue", "ticket", "part", "dev_user"]:
        raise ValueError(f"Invalid namespace '{namespace}'. Must be one of: article, issue, ticket, part, dev_user")
    
    try:
        await ctx.info(f"Searching DevRev for '{query}' in namespace '{namespace}'")
        
        response = make_devrev_request(
            SEARCH_HYBRID,
            {"query": query, "namespace": namespace}
        )
        
        if response.status_code != 200:
            error_text = response.text
            await ctx.error(f"Search failed with status {response.status_code}: {error_text}")
            raise ValueError(f"Search failed with status {response.status_code}: {error_text}")
        
        search_results = response.json()
        parsed_results = _parse_search_results(search_results, namespace)
        
        await ctx.info(f"Search completed successfully with {len(parsed_results.get('results', []))} results")
        
        return json.dumps(parsed_results, indent=2)
    
    except Exception as e:
        await ctx.error(f"Search operation failed: {str(e)}")
        raise


def _parse_search_results(raw_results: Dict[str, Any], namespace: str) -> Dict[str, Any]:
    """
    Parse raw search results to extract useful information.
    
    Args:
        raw_results: Raw search results from DevRev API
        namespace: The namespace that was searched
        
    Returns:
        Parsed results with key information extracted
    """
    parsed = {
        "query_info": {
            "namespace": namespace,
            "total_results": len(raw_results.get("results", []))
        },
        "results": []
    }
    
    for result in raw_results.get("results", []):
        if result.get("type") == "work" and "work" in result:
            work = result["work"]
            parsed_result = _parse_work_result(work)
            parsed["results"].append(parsed_result)
        elif result.get("type") == "article" and "article" in result:
            article = result["article"]
            parsed_result = _parse_article_result(article)
            parsed["results"].append(parsed_result)
        else:
            # For other types, include basic info
            parsed_result = {
                "type": result.get("type", "unknown"),
                "id": result.get("id"),
                "snippet": result.get("snippet", "")
            }
            parsed["results"].append(parsed_result)
    
    return parsed


def _parse_work_result(work: Dict[str, Any]) -> Dict[str, Any]:
    """Parse work (ticket/issue) search result."""
    return {
        "type": "work",
        "work_type": work.get("type"),
        "id": work.get("id"),
        "display_id": work.get("display_id"),
        "title": work.get("title"),
        "severity": work.get("severity"),
        "stage": work.get("stage", {}).get("name"),
        "owned_by": [
            {
                "name": owner.get("display_name"),
                "email": owner.get("email"),
                "id": owner.get("id")
            }
            for owner in work.get("owned_by", [])
        ],
        "rev_org": {
            "name": work.get("rev_org", {}).get("display_name"),
            "id": work.get("rev_org", {}).get("id")
        }
    }


def _parse_article_result(article: Dict[str, Any]) -> Dict[str, Any]:
    """Parse article search result."""
    return {
        "type": "article",
        "id": article.get("id"),
        "display_id": article.get("display_id"),
        "title": article.get("title"),
        "status": article.get("status"),
        "authored_by": {
            "name": article.get("authored_by", {}).get("display_name"),
            "email": article.get("authored_by", {}).get("email"),
            "id": article.get("authored_by", {}).get("id")
        }
    }