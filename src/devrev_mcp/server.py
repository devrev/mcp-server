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
from .utils import make_devrev_request, search_part_by_name, get_current_user_id

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
                    "namespace": {"type": "string", "enum": ["article", "issue", "ticket"]},
                },
                "required": ["query", "namespace"],
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
            name="create_issue",
            description="Create a DevRev issue with the specified title. The part_name parameter is used to search for and identify the appropriate part ID, and the issue will be automatically assigned to the currently authenticated user.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "part_name": {"type": "string"},
                },
                "required": ["title", "part_name"],
            },
        )
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
    elif name == "create_issue":
        if not arguments:
            raise ValueError("Missing arguments")

        title = arguments.get("title")
        part_name = arguments.get("part_name")
        
        if not title:
            raise ValueError("Missing title parameter")
            
        if not part_name:
            raise ValueError("Missing part_name parameter")
            
        # Search for part by name
        success, part_id, error_message = search_part_by_name(part_name)
        if not success:
            return [
                types.TextContent(
                    type="text",
                    text=error_message
                )
            ]
            
        # Get current user ID
        success, user_id, error_message = get_current_user_id()
        if not success:
            return [
                types.TextContent(
                    type="text",
                    text=error_message
                )
            ]
    
        response = make_devrev_request(
            "works.create",
            {
                "type": "issue",
                "title": title,
                "applies_to_part": part_id,
                "owned_by": [user_id]
            }
        )
        
        if response.status_code != 201:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Create issue failed with status {response.status_code}: {error_text}"
                )
            ]

        issue_info = response.json()
        return [
            types.TextContent(
                type="text",
                text=f"Issue created successfully with ID: {issue_info['display_id']} Info: {issue_info}"
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
