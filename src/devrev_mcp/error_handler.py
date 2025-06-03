"""
DevRev MCP Error Handler

Provides standardized error handling for resources and tools.
"""

import json
from typing import Dict, Optional
from functools import wraps
from fastmcp import Context


class DevRevMCPError(Exception):
    """Base exception for DevRev MCP errors."""
    def __init__(self, message: str, error_code: str = "UNKNOWN", details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ResourceNotFoundError(DevRevMCPError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict] = None):
        message = f"{resource_type} {resource_id} not found"
        super().__init__(message, "RESOURCE_NOT_FOUND", details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class APIError(DevRevMCPError):
    """Raised when DevRev API returns an error."""
    def __init__(self, endpoint: str, status_code: int, response_text: str):
        message = f"DevRev API error on {endpoint}: HTTP {status_code}"
        details = {"status_code": status_code, "response": response_text}
        super().__init__(message, "API_ERROR", details)
        self.endpoint = endpoint
        self.status_code = status_code


def create_error_response(
    error: Exception, 
    resource_type: str = "resource", 
    resource_id: str = "",
    additional_data: Optional[Dict] = None
) -> str:
    """
    Create a standardized JSON error response.
    
    Args:
        error: The exception that occurred
        resource_type: Type of resource (ticket, artifact, etc.)
        resource_id: ID of the resource that failed
        additional_data: Additional data to include in error response
    
    Returns:
        JSON string containing error information
    """
    error_data = {
        "error": True,
        "error_type": type(error).__name__,
        "message": str(error),
        "resource_type": resource_type,
        "resource_id": resource_id,
        "timestamp": None  # Could add timestamp if needed
    }
    
    # Add specific error details for known error types
    if isinstance(error, DevRevMCPError):
        error_data["error_code"] = error.error_code
        error_data["details"] = error.details
    
    if isinstance(error, APIError):
        error_data["api_endpoint"] = error.endpoint
        error_data["http_status"] = error.status_code
    
    # Include any additional data
    if additional_data:
        error_data.update(additional_data)
    
    return json.dumps(error_data, indent=2)


def resource_error_handler(resource_type: str):
    """
    Decorator for resource handlers that provides standardized error handling.
    
    Args:
        resource_type: The type of resource (e.g., "ticket", "artifact")
    
    Returns:
        Decorated function with error handling
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract resource_id from function arguments
            resource_id = args[0] if args else "unknown"
            ctx = None
            
            # Find Context in arguments
            for arg in args:
                if isinstance(arg, Context):
                    ctx = arg
                    break
            
            try:
                return await func(*args, **kwargs)
            
            except DevRevMCPError as e:
                if ctx:
                    await ctx.error(f"{resource_type} error: {e.message}")
                return create_error_response(e, resource_type, resource_id)
            
            except Exception as e:
                if ctx:
                    await ctx.error(f"Unexpected error in {resource_type} {resource_id}: {str(e)}")
                
                # Convert to standardized error
                mcp_error = DevRevMCPError(
                    f"Unexpected error: {str(e)}", 
                    "INTERNAL_ERROR",
                    details={"original_exception": type(e).__name__, "cause": str(e)}
                )
                return create_error_response(mcp_error, resource_type, resource_id)
        
        return wrapper
    return decorator


def tool_error_handler(tool_name: str):
    """
    Decorator for tool handlers that provides standardized error handling.
    
    Args:
        tool_name: The name of the tool
    
    Returns:
        Decorated function with error handling
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = None
            
            # Find Context in arguments or kwargs
            for arg in args:
                if isinstance(arg, Context):
                    ctx = arg
                    break
            
            if not ctx and 'ctx' in kwargs:
                ctx = kwargs['ctx']
            
            try:
                return await func(*args, **kwargs)
            
            except DevRevMCPError as e:
                if ctx:
                    await ctx.error(f"{tool_name} error: {e.message}")
                raise  # Re-raise for tools since they can handle exceptions
            
            except Exception as e:
                if ctx:
                    await ctx.error(f"Unexpected error in {tool_name}: {str(e)}")
                
                # Convert to standardized error and re-raise
                raise DevRevMCPError(
                    f"Tool {tool_name} failed: {str(e)}", 
                    "TOOL_ERROR"
                ) from e
        
        return wrapper
    return decorator


def handle_api_response(response, endpoint: str, expected_status: int = 200):
    """
    Handle DevRev API response and raise appropriate errors.
    
    Args:
        response: The requests Response object
        endpoint: API endpoint that was called
        expected_status: Expected HTTP status code (default 200)
    
    Raises:
        APIError: If the response status is not as expected
    """
    if response.status_code != expected_status:
        raise APIError(endpoint, response.status_code, response.text)
    
    return response


# Utility function to check and validate resource IDs
def validate_resource_id(resource_id: str, resource_type: str) -> str:
    """
    Validate and normalize resource IDs.
    
    Args:
        resource_id: The resource ID to validate
        resource_type: Type of resource for error messages
    
    Returns:
        Normalized resource ID
    
    Raises:
        ResourceNotFoundError: If resource ID is invalid
    """
    if not resource_id or not isinstance(resource_id, str):
        raise ResourceNotFoundError(
            resource_type, 
            str(resource_id), 
            {"reason": "Invalid or empty resource ID"}
        )
    
    resource_id = resource_id.strip()
    if not resource_id:
        raise ResourceNotFoundError(
            resource_type, 
            resource_id, 
            {"reason": "Empty resource ID after normalization"}
        )
    
    return resource_id