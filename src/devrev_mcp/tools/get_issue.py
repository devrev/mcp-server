"""
DevRev Get Issue Tool

Tool for retrieving DevRev issue information with enriched timeline and linked work items.
"""

from fastmcp import Context
from ..resources.issue import issue
from ..cache import devrev_cache


async def get_issue(issue_id: str, ctx: Context) -> str:
    """
    Get a DevRev issue by ID with enriched timeline entries and linked work items.
    
    Args:
        issue_id: The DevRev issue ID - accepts ISS-9031, 9031, or full don:core format
        ctx: FastMCP context
    
    Returns:
        JSON string containing the enriched issue data with timeline and links
    """
    # Extract numeric ID from various formats
    if issue_id.startswith("ISS-"):
        issue_number = issue_id[4:]
    elif issue_id.startswith("don:core:"):
        # Extract from full don format
        issue_number = issue_id.split("/")[-1]
    else:
        # Assume it's already a numeric ID
        issue_number = issue_id
    
    # Use the enriched issue resource
    return await issue(issue_number, ctx, devrev_cache)