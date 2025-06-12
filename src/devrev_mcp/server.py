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
            name="get_work",
            description="Get all information about a DevRev work item (issue, ticket) using its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "The DevRev ID of the work item"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="create_work",
            description="Create a new work item (issue, ticket) in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["issue", "ticket"]},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "applies_to_part": {"type": "string", "description": "The DevRev ID of the part to which the work item applies"},
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the users who are assigned to the work item"}
                },
                "required": ["type", "title", "applies_to_part"],
            },
        ),
        types.Tool(
            name="update_work",
            description="Update an existing work item (issue, ticket) in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["issue", "ticket"]},
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "applies_to_part": {"type": "string", "description": "The DevRev ID of the part to which the work item applies"},
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the users who are assigned to the work item"},
                },
                "required": ["id", "type"],
            },
        ),
        types.Tool(
            name="get_part",
            description="Get information about a part (enhancement) in DevRev using its ID",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "The DevRev ID of the part"}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="create_part",
            description="Create a new part (enhancement) in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["enhancement"]},
                    "name": {"type": "string"},
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the users assigned to the part"},
                    "parent_part": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the parent parts"},
                    "description": {"type": "string", "description": "The description of the part"},
                },
                "required": ["type", "name", "owned_by", "parent_part"],
            },
        ),
        types.Tool(
            name="update_part",
            description="Update an existing part (enhancement) in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["enhancement"]},
                    "id": {"type": "string", "description": "The DevRev ID of the part"},
                    "name": {"type": "string", "description": "The name of the part"},
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the users assigned to the part"},
                    "description": {"type": "string", "description": "The description of the part"},
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
            {
                "query": query, 
                "namespace": namespace
            }
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
    elif name == "get_work":
        if not arguments:
            raise ValueError("Missing arguments")

        id = arguments.get("id")
        if not id:
            raise ValueError("Missing id parameter")
        
        response = make_devrev_request(
            "works.get",
            {
                "id": id
            }
        )
        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Get object failed with status {response.status_code}: {error_text}"
                )
            ]
        
        return [
            types.TextContent(
                type="text",
                text=f"Object information for '{id}':\n{response.json()}"
            )
        ]
    elif name == "create_work":
        if not arguments:
            raise ValueError("Missing arguments")

        type = arguments.get("type")
        if not type:
            raise ValueError("Missing type parameter")

        title = arguments.get("title")
        if not title:
            raise ValueError("Missing title parameter")

        applies_to_part = arguments.get("applies_to_part")
        if not applies_to_part:
            raise ValueError("Missing applies_to_part parameter")

        body = arguments.get("body", "")
        owned_by = arguments.get("owned_by", [])

        response = make_devrev_request(
            "works.create",
            {
                "type": type,
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
    elif name == "update_work":
        if not arguments:
            raise ValueError("Missing arguments")

        id = arguments.get("id")
        if not id:
            raise ValueError("Missing id parameter")
        
        type = arguments.get("type")
        if not type:
            raise ValueError("Missing type parameter")
        
        title = arguments.get("title")
        body = arguments.get("body")
        sprint = arguments.get("sprint")

        payload = {"id": id, "type": type}
        if title:
            payload["title"] = title
        if body:
            payload["body"] = body
        if sprint:
            payload["sprint"] = sprint
            
        response = make_devrev_request(
            "works.update",
            payload
        )

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
    elif name == "get_part":
        if not arguments:
            raise ValueError("Missing arguments")

        id = arguments.get("id")
        if not id:
            raise ValueError("Missing id parameter")
        
        response = make_devrev_request(
            "parts.get",
            {
                "id": id
            }
        )

        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Get part failed with status {response.status_code}: {error_text}"
                )
            ]
        
        return [
            types.TextContent(
                type="text",
                text=f"Part information for '{id}':\n{response.json()}"
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

        part_name = arguments.get("name")
        if not part_name:
            raise ValueError("Missing name parameter")
        payload["name"] = part_name

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

        part_name = arguments.get("name")
        if part_name:
            payload["name"] = part_name

        owned_by = arguments.get("owned_by")
        if owned_by:
            payload["owned_by"] = owned_by
        
        description = arguments.get("description")
        if description:
            payload["description"] = description

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
                text=f"Part updated successfully: {id}"
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
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
