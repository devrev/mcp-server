"""
DevRev Ticket Artifacts Resource Handler

Provides access to all artifacts associated with a specific ticket.
"""

import json
from fastmcp import Context
from .ticket import ticket as ticket_resource
from ..error_handler import resource_error_handler


@resource_error_handler("ticket_artifacts")
async def ticket_artifacts(ticket_id: str, ctx: Context, devrev_cache: dict) -> str:
    """
    Access all artifacts for a ticket.
    
    Args:
        ticket_id: The DevRev ticket ID (e.g., 12345 for TKT-12345)
        ctx: FastMCP context
        devrev_cache: Cache dictionary for storing results
    
    Returns:
        JSON string containing artifacts with navigation links
    """
    # Get ticket data to extract artifacts
    ticket_data_str = await ticket_resource(ticket_id, ctx, devrev_cache)
    
    ticket_data = json.loads(ticket_data_str)
    artifacts = ticket_data.get("artifacts", [])
    
    # Add navigation links to each artifact
    for artifact in artifacts:
        artifact_id = artifact.get("id", "").split("/")[-1] if artifact.get("id") else ""
        if artifact_id:
            artifact["links"] = {
                "self": f"devrev://artifacts/{artifact_id}",
                "ticket": f"devrev://tickets/{ticket_id}"
            }
    
    result = {
        "artifacts": artifacts,
        "links": {
            "ticket": f"devrev://tickets/{ticket_id}"
        }
    }
    
    return json.dumps(result, indent=2) 