"""
Copyright (c) 2025 DevRev, Inc.
SPDX-License-Identifier: MIT

This module implements the MCP server for DevRev integration.
"""

import asyncio
import os
import requests

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from .utils import make_devrev_request

server = Server("devrev_mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="search",
            description="Search DevRev using the provided query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "namespace": {"type": "string", "enum": ["article", "issue", "ticket", "part", "dev_user"]},
                },
                "required": ["query", "namespace"],
            },
        ),
        types.Tool(
            name="get_current_user",
            description="Get the current user's information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="get_object",
            description="Get all information about a DevRev issue and ticket using its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="create_object",
            description="Create a new isssue or ticket in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["issue", "ticket"]},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "applies_to_part": {"type": "string"},
                    "owned_by": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["type", "title", "applies_to_part"],
            },
        ),
        types.Tool(
            name="update_object",
            description="Update an existing issue or ticket in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["issue", "ticket"]},
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["id", "type"],
            },
        ),
        types.Tool(
            name="list_works",
            description="List all works in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "array", "items": {"type": "string", "enum": ["issue", "ticket"]}, "description": "The type of works to list"},
                    "applies_to_part": {"type": "array", "items": {"type": "string"}, "description": "The part IDs of the works to list"},
                    "created_by": {"type": "array", "items": {"type": "string"}, "description": "The user IDs of the creators of the works to list"},
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The user IDs of the owners of the works to list"},
                    "stage": {"type": "array", "items": {"type": "string"}, "description": "The stage names of the works to list"},
                    "state": {"type": "array", "items": {"type": "string"}, "description": "The state names of the works to list"},
                    "limit": {"type": "integer", "description": "The maximum number of works to list"},
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get_part",
            description="Get an existing part in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="create_part",
            description="Create a new part in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["enhancement"]},
                    "name": {"type": "string"},
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The user IDs of the owners of the part"},
                    "parent_part": {"type": "array", "items": {"type": "string"}, "description": "The part IDs of the parent parts"},
                    "description": {"type": "string", "description": "The description of the part"},
                },
                "required": ["type", "name", "owned_by", "parent_part"],
            },
        ),
        types.Tool(
            name="update_part",
            description="Update an existing part in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["enhancement"]},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The user IDs of the owners of the part"},
                    "target_close_date": {"type": "string", "description": "The target closed date of the part, for example: 2025-06-03T00:00:00Z"},
                    "target_start_date": {"type": "string", "description": "The target start date of the part, for example: 2025-06-03T00:00:00Z"},
                },
                "required": ["id", "type"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if name == "search":
        if not arguments:
            raise ValueError("Missing arguments")

        query = arguments.get("query")
        if not query:
            raise ValueError("Missing query parameter")
        
        namespace = arguments.get("namespace")
        if not namespace:
            raise ValueError("Missing namespace parameter")

        response = make_devrev_request(
            "search.hybrid",
            {"query": query, "namespace": namespace}
        )
        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Search failed with status {response.status_code}: {error_text}"
                )
            ]
        
        search_results = response.json()
        return [
            types.TextContent(
                type="text",
                text=f"Search results for '{query}':\n{search_results}"
            )
        ]
    elif name == "get_current_user":
        response = make_devrev_request(
            "dev-users.self",
            {}
        )
        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Get current user failed with status {response.status_code}: {error_text}"
                )
            ]
        user_info = response.json()
        return [
            types.TextContent(
                type="text",
                text=f"Current user information: {user_info}"
            )
        ]
    elif name == "get_object":
        if not arguments:
            raise ValueError("Missing arguments")

        id = arguments.get("id")
        if not id:
            raise ValueError("Missing id parameter")
        
        response = make_devrev_request(
            "works.get",
            {"id": id}
        )
        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Get object failed with status {response.status_code}: {error_text}"
                )
            ]
        
        object_info = response.json()
        return [
            types.TextContent(
                type="text",
                text=f"Object information for '{id}':\n{object_info}"
            )
        ]
    elif name == "create_object":
        if not arguments:
            raise ValueError("Missing arguments")

        # Mandatory fields
        object_type = arguments.get("type")
        if not object_type:
            raise ValueError("Missing type parameter")

        title = arguments.get("title")
        if not title:
            raise ValueError("Missing title parameter")

        applies_to_part = arguments.get("applies_to_part")
        if not applies_to_part:
            raise ValueError("Missing applies_to_part parameter")

        # Optional fields
        body = arguments.get("body", "")
        owned_by = arguments.get("owned_by", [])

        response = make_devrev_request(
            "works.create",
            {
                "type": object_type,
                "title": title,
                "body": body,
                "applies_to_part": applies_to_part,
                "owned_by": owned_by
            }
        )
        if response.status_code != 201:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Create object failed with status {response.status_code}: {error_text}"
                )
            ]

        return [
            types.TextContent(
                type="text",
                text=f"Object created successfully: {response.json()}"
            )
        ]
    elif name == "update_object":
        # Update mandatory fields
        if not arguments:
            raise ValueError("Missing arguments")

        id = arguments.get("id")
        if not id:
            raise ValueError("Missing id parameter")
        
        object_type = arguments.get("type")
        if not object_type:
            raise ValueError("Missing type parameter")
        
        # Update title and body
        title = arguments.get("title")
        body = arguments.get("body")
        
        # Build request payload with only the fields that have values
        update_payload = {"id": id, "type": object_type}
        if title:
            update_payload["title"] = title
        if body:
            update_payload["body"] = body
            
        # Make devrev request to update the object
        response = make_devrev_request(
            "works.update",
            update_payload
        )

        # Check if the request was successful
        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Update object failed with status {response.status_code}: {error_text}"
                )
            ]
        
        return [
            types.TextContent(
                type="text",
                text=f"Object updated successfully: {id}"
            )
        ]
    elif name == "list_works":
        if not arguments:
            raise ValueError("Missing arguments")

        payload = {}

        type = arguments.get("type")
        if type:
            payload["type"] = type

        applies_to_part = arguments.get("applies_to_part")
        if applies_to_part:
            payload["applies_to_part"] = applies_to_part

        created_by = arguments.get("created_by")
        if created_by:
            payload["created_by"] = created_by

        owned_by = arguments.get("owned_by")
        if owned_by:
            payload["owned_by"] = owned_by

        stage = arguments.get("stage")
        if stage:
            payload["stage"] = {"name": stage}

        state = arguments.get("state")
        if state:
            payload["state"] = state

        limit = arguments.get("limit")
        if limit:
            payload["limit"] = limit

        response = make_devrev_request(
            "works.list",
            payload
        )

        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"List works failed with status {response.status_code}: {error_text}"
                )
            ]
        return [
            types.TextContent(
                type="text",
                text=f"Works listed successfully: {response.json()}"
            )
        ]
    elif name == "get_part":
        if not arguments:
            raise ValueError("Missing arguments")

        id = arguments.get("id")
        if not id:
            raise ValueError("Missing id parameter")
        
        response = make_devrev_request(
            "parts.get",
            {"id": id}
        )

        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Get part failed with status {response.status_code}: {error_text}"
                )
            ]
        
        part_info = response.json()
        return [
            types.TextContent(
                type="text",
                text=f"Part information for '{id}':\n{part_info}"
            )
        ]
    elif name == "create_part":
        if not arguments:
            raise ValueError("Missing arguments")

        payload = {}

        type = arguments.get("type")
        if not type:
            raise ValueError("Missing type parameter")
        payload["type"] = type

        name = arguments.get("name")
        if not name:
            raise ValueError("Missing name parameter")
        payload["name"] = name

        owned_by = arguments.get("owned_by")
        if not owned_by:
            raise ValueError("Missing owned_by parameter")
        payload["owned_by"] = owned_by

        parent_part = arguments.get("parent_part")
        if not parent_part:
            raise ValueError("Missing parent_part parameter")
        payload["parent_part"] = parent_part
        
        description = arguments.get("description")
        if description:
            payload["description"] = description

        response = make_devrev_request(
            "parts.create",
            payload
        )

        if response.status_code != 201:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Create part failed with status {response.status_code}: {error_text}"
                )
            ]
        
        return [
            types.TextContent(
                type="text",
                text=f"Part created successfully: {response.json()}"
            )
        ]
    elif name == "update_part":
        if not arguments:
            raise ValueError("Missing arguments")

        payload = {}
        
        id = arguments.get("id")
        if not id:
            raise ValueError("Missing id parameter")
        payload["id"] = id

        type = arguments.get("type")
        if not type:
            raise ValueError("Missing type parameter")
        payload["type"] = type

        name = arguments.get("name")
        if name:
            payload["name"] = name

        description = arguments.get("description")
        if description:
            payload["description"] = description

        owned_by = arguments.get("owned_by")
        if owned_by:
            payload["owned_by"] = owned_by

        target_close_date = arguments.get("target_close_date")
        if target_close_date:
            payload["target_close_date"] = target_close_date

        target_start_date = arguments.get("target_start_date")
        if target_start_date:
            payload["target_start_date"] = target_start_date

        response = make_devrev_request(
            "parts.update",
            payload
        )

        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Update part failed with status {response.status_code}: {error_text}"
                )
            ]
        return [
            types.TextContent(
                type="text",
                text=f"Part updated successfully: {response.json()}"
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="devrev_mcp",
                server_version="0.1.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
