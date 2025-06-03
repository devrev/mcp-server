"""
DevRev Artifact Resource Handler

Provides specialized resource access for DevRev artifacts with metadata and download URLs.
"""

import json
from fastmcp import Context
from ..utils import make_devrev_request
from ..error_handler import resource_error_handler, handle_api_response, validate_resource_id
from ..endpoints import ARTIFACTS_GET, ARTIFACTS_LOCATE


@resource_error_handler("artifact")
async def artifact(artifact_id: str, ctx: Context, devrev_cache: dict) -> str:
    """
    Access DevRev artifact metadata.
    
    Args:
        artifact_id: The DevRev artifact ID
        ctx: FastMCP context
        devrev_cache: Cache dictionary for storing results
    
    Returns:
        JSON string containing the artifact metadata
    """
    # Validate the artifact ID
    artifact_id = validate_resource_id(artifact_id, "artifact")
    
    cache_key = f"artifact:{artifact_id}"
    
    # Check cache first
    cached_value = devrev_cache.get(cache_key)
    if cached_value is not None:
        await ctx.info(f"Retrieved artifact {artifact_id} from cache")
        return cached_value
    
    await ctx.info(f"Fetching artifact {artifact_id} from DevRev API")
    
    # For artifacts, use artifacts.get endpoint
    response = make_devrev_request(
        ARTIFACTS_GET,
        {"id": artifact_id}
    )
    
    # Handle API response with standardized error handling
    handle_api_response(response, ARTIFACTS_GET)
    
    result = response.json()
    
    # Try to get download URL if available through artifacts.locate
    artifact_info = result.get("artifact", {})
    if artifact_info and not any(key in artifact_info.get("file", {}) for key in ["download_url", "url"]):
        try:
            await ctx.info(f"Attempting to get download URL for artifact {artifact_id}")
            locate_response = make_devrev_request(
                ARTIFACTS_LOCATE,
                {"id": artifact_id}
            )
            
            if locate_response.status_code == 200:
                locate_data = locate_response.json()
                locate_artifact = locate_data.get("artifact", {})
                if locate_artifact:
                    # Merge locate data into the main artifact data
                    if "download_url" in locate_artifact:
                        artifact_info["download_url"] = locate_artifact["download_url"]
                    if "file" in locate_artifact and "download_url" in locate_artifact["file"]:
                        if "file" not in artifact_info:
                            artifact_info["file"] = {}
                        artifact_info["file"]["download_url"] = locate_artifact["file"]["download_url"]
                    await ctx.info(f"Successfully added download URL for artifact {artifact_id}")
            else:
                await ctx.info(f"artifacts.locate not available for {artifact_id}: HTTP {locate_response.status_code}")
        except Exception as locate_error:
            await ctx.info(f"Could not locate download URL for artifact {artifact_id}: {str(locate_error)}")
            # Continue without download URL
    
    
    # Cache the result
    cache_value = json.dumps(result, indent=2)
    devrev_cache.set(cache_key, cache_value)
    await ctx.info(f"Successfully retrieved and cached artifact: {artifact_id}")
    
    return cache_value