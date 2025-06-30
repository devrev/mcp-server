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
            name="get_current_user",
            description="Fetch the current DevRev user details. When the user specifies 'me' in the query, this tool should be called to get the user details.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="search",
            description="Search DevRev using the provided query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "namespace": {
                        "type": "string", 
                        "enum": ["article", "issue", "ticket", "part", "dev_user", "account", "rev_org"],
                        "description": "The namespace to search in. Use this to specify the type of object to search for."
                    },
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
                    "modified_by": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the users who modified the work item"},
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the users who are assigned to the work item"},
                    "stage": {"type": "string", "description": "The stage name of the work item. Use valid_stage_transition tool to get the list of valid stages you an update to."},
                },
                "required": ["id", "type"],
            },
        ),
        types.Tool(
            name="list_works",
            description="List all work items (issues, tickets) in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "array", "items": {"type": "string", "enum": ["issue", "ticket"]}, "description": "The type of works to list"},
                    "cursor": {
                        "type": "object",
                        "properties": {
                            "next_cursor": {"type": "string", "description": "The cursor to use for pagination. If not provided, iteration begins from the first page."},
                            "mode": {"type": "string", "enum": ["after", "before"], "description": "The mode to iterate after the cursor or before the cursor ."},
                        },
                        "required": ["next_cursor", "mode"],
                        "description": "The cursor to use for pagination. If not provided, iteration begins from the first page. In the output you get next_cursor, use it and the correct mode to get the next or previous page. You can use these to loop through all the pages."
                    },
                    "applies_to_part": {"type": "array", "items": {"type": "string"}, "description": "The part IDs of the works to list"},
                    "created_by": {"type": "array", "items": {"type": "string"}, "description": "The user IDs of the creators of the works to list"},
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The user IDs of the owners of the works to list"},
                    "state": {"type": "array", "items": {"type": "string", "enum": ["open", "closed", "in_progress"]}, "description": "The state names of the works to list"},
                    "modified_by": {"type": "array", "items": {"type": "string"}, "description": "The user IDs of the users who modified the works to list"},
                    "sla_summary": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the SLA summary range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the SLA summary range, for example: 2025-06-03T00:00:00Z"},
                        },
                        "required": ["after", "before"],
                        "description": "Service Level Agreement summary filter on issues to list."
                    },
                    "sort_by": {"type": "array", "items": {"type": "string", "enum": ["target_start_date:asc", "target_start_date:desc", "target_close_date:asc", "target_close_date:desc", "actual_start_date:asc", "actual_start_date:desc", "actual_close_date:asc", "actual_close_date:desc", "created_date:asc", "created_date:desc"]}, "description": "The field (and the order) to sort the works by, in the sequence of the array elements"},
                    "rev_orgs": {"type": "array", "items": {"type": "string"}, "description": "The rev_org IDs of the customer rev_orgs filter on Issues and Tickets to list. Use this filter for issues and tickets that are related to a customer rev_org."},
                    "target_close_date": {
                        "type": "object", 
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the target close date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the target close date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "required": ["after", "before"]
                    },
                    "target_start_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the target start date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the target start date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "description": "The target start date range can only be used for issues. Do not use this field for tickets.",
                        "required": ["after", "before"]
                    },
                    "actual_close_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the actual close date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the actual close date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "required": ["after", "before"]
                    },
                    "actual_start_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the actual start date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the actual start date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "description": "The actual start date range can only be used for issues. Do not use this field for tickets.",
                        "required": ["after", "before"]
                    },
                    "created_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the created date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the created date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "required": ["after", "before"]
                    },
                    "modified_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the modified date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the modified date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "required": ["after", "before"]
                    },
                },
                "required": ["type"],
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
                    "stage": {"type": "string", "description": "The stage DevRev ID of the part. Use valid_stage_transition tool to get the list of valid stages you an update to."},
                },
                "required": ["id", "type"],
            },
        ),
        types.Tool(
            name="list_parts",
            description="List all parts (enhancements) in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["enhancement"], "description": "The type of parts to list"},
                    "cursor": {
                        "type": "object",
                        "properties": {
                            "next_cursor": {"type": "string", "description": "The cursor to use for pagination. If not provided, iteration begins from the first page."},
                            "mode": {"type": "string", "enum": ["after", "before"], "description": "The mode to iterate after the cursor or before the cursor ."},
                        },
                        "required": ["next_cursor", "mode"],
                        "description": "The cursor to use for pagination. If not provided, iteration begins from the first page. In the output you get next_cursor, use it and the correct mode to get the next or previous page. You can use these to loop through all the pages."
                    },
                    "owned_by": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the users assigned to the parts to list"},
                    "parent_part": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the parent parts to of the parts to list"},
                    "created_by": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the users who created the parts to list"},
                    "modified_by": {"type": "array", "items": {"type": "string"}, "description": "The DevRev IDs of the users who modified the parts to list"},
                    "sort_by": {"type": "array", "items": {"type": "string", "enum": ["target_close_date:asc", "target_close_date:desc", "target_start_date:asc", "target_start_date:desc", "actual_close_date:asc", "actual_close_date:desc", "actual_start_date:asc", "actual_start_date:desc", "created_date:asc", "created_date:desc", "modified_date:asc", "modified_date:desc"]}, "description": "The field (and the order) to sort the parts by, in the sequence of the array elements"},
                    "accounts": {"type": "array", "items": {"type": "string"}, "description": "The account IDs of the accounts filter on parts to list"},
                    "target_close_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the target close date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the target close date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "required": ["after", "before"]
                    },
                    "target_start_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the target start date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the target start date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "required": ["after", "before"]
                    },
                    "actual_close_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the actual close date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the actual close date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "required": ["after", "before"]
                    },
                    "actual_start_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the actual start date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the actual start date range, for example: 2025-06-03T00:00:00Z"},
                        }, 
                        "required": ["after", "before"]
                    },
                },
                "required": ["type"],
            },
        ),
        types.Tool(
            name="list_meetings",
            description="List meetings in DevRev",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["amazon_connect", "google_meet", "offline", "other", "teams", "zoom"]},
                        "description": "Filters for meeting on specified channels"
                    },
                    "created_by": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filters for meetings created by the specified user DevRev IDs"
                    },
                    "created_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the created date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the created date range, for example: 2025-06-03T00:00:00Z"}
                        },
                        "required": ["after", "before"]
                    },
                    "cursor": {
                        "type": "object",
                        "properties": {
                            "next_cursor": {"type": "string", "description": "The cursor to use for pagination. If not provided, iteration begins from the first page."},
                            "mode": {"type": "string", "enum": ["after", "before"], "description": "The mode to iterate after the cursor or before the cursor"}
                        },
                        "required": ["next_cursor", "mode"]
                    },
                    "ended_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the ended date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the ended date range, for example: 2025-06-03T00:00:00Z"}
                        },
                        "required": ["after", "before"]
                    },
                    "external_ref": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filters for meetings with the provided external_ref(s)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The maximum number of meetings to return"
                    },
                    "members": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter for meeting on specified Member Ids"
                    },
                    "modified_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the modified date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the modified date range, for example: 2025-06-03T00:00:00Z"}
                        },
                        "required": ["after", "before"]
                    },
                    "organizer": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter for meeting on specified organizers"
                    },
                    "scheduled_date": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string", "description": "The start date of the scheduled date range, for example: 2025-06-03T00:00:00Z"},
                            "before": {"type": "string", "description": "The end date of the scheduled date range, for example: 2025-06-03T00:00:00Z"}
                        },
                        "required": ["after", "before"]
                    },
                    "sort_by": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["target_start_date:asc", "target_start_date:desc", "target_close_date:asc", "target_close_date:desc", "actual_start_date:asc", "actual_start_date:desc", "actual_close_date:asc", "actual_close_date:desc", "created_date:asc", "created_date:desc", "modified_date:asc", "modified_date:desc"]
                        },
                        "description": "The field (and the order) to sort the meetings by, in the sequence of the array elements"
                    },
                    "state": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["cancelled", "completed", "no_show", "ongoing", "rejected", "scheduled", "rescheduled", "waiting"]},
                        "description": "Filters for meeting on specified state or outcomes"
                    }
                }
            }
        ),
        types.Tool(
            name="valid_stage_transition",
            description="gets a list of valid stage transition for a given work item (issue, ticket) or part (enhancement). Use this before updating stage of the work item or part to ensure the transition is valid.",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["issue", "ticket", "enhancement"]},
                    "id": {"type": "string", "description": "The DevRev ID of the work item (issue, ticket) or part (enhancement)"},
                },
                "required": ["type", "id"]
            }
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
    if name == "get_current_user":
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

        return [
            types.TextContent(
                type="text",
                text=f"Current DevRev user details: {response.json()}"
            )
        ]
    elif name == "search":
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
        
        payload = {}

        id = arguments.get("id")
        if not id:
            raise ValueError("Missing id parameter")
        payload["id"] = id
        
        type = arguments.get("type")
        if not type:
            raise ValueError("Missing type parameter")
        payload["type"] = type

        title = arguments.get("title")
        if title:
            payload["title"] = title

        body = arguments.get("body", "")
        if body:
            payload["body"] = body

        modified_by = arguments.get("modified_by")
        if modified_by:
            payload["modified_by"] = modified_by

        owned_by = arguments.get("owned_by")
        if owned_by:
            payload["owned_by"] = owned_by

        applies_to_part = arguments.get("applies_to_part", [])
        if applies_to_part:
            payload["applies_to_part"] = applies_to_part

        stage = arguments.get("stage")
        if stage:
            payload["stage"] = {"name": stage}

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
    elif name == "list_works":
        payload = {}
        payload["issue"] = {}
        payload["ticket"] = {}
        
        type = arguments.get("type")
        if not type:
            raise ValueError("Missing type parameter")
        payload["type"] = type

        cursor = arguments.get("cursor")
        if cursor:
            payload["cursor"] = cursor["next_cursor"]
            payload["mode"] = cursor["mode"]

        applies_to_part = arguments.get("applies_to_part")
        if applies_to_part:
            payload["applies_to_part"] = applies_to_part

        created_by = arguments.get("created_by")
        if created_by:
            payload["created_by"] = created_by

        modified_by = arguments.get("modified_by")
        if modified_by:
            payload["modified_by"] = modified_by

        owned_by = arguments.get("owned_by")
        if owned_by:
            payload["owned_by"] = owned_by

        state = arguments.get("state")
        if state:
            payload["state"] = state

        sla_summary = arguments.get("sla_summary")
        if sla_summary:
            payload["issue"]["sla_summary"] = {"target_time": {"type": "range", "after": sla_summary["after"], "before": sla_summary["before"]}}
        
        sort_by = arguments.get("sort_by")
        if sort_by:
            payload["sort_by"] = sort_by

        rev_orgs = arguments.get("rev_orgs")
        if rev_orgs and rev_orgs != []:
            if 'ticket' in type:
                payload["ticket"]["rev_org"] = rev_orgs

            if 'issue' in type:
                payload["issue"]["rev_orgs"] = rev_orgs

        target_close_date = arguments.get("target_close_date")
        if target_close_date:
            payload["target_close_date"] = {"type": "range", "after": target_close_date["after"], "before": target_close_date["before"]}
        
        target_start_date = arguments.get("target_start_date")
        if target_start_date:
            if 'issue' in type:
                payload["issue"]["target_start_date"] = {"type": "range", "after": target_start_date["after"], "before": target_start_date["before"]}

        actual_close_date = arguments.get("actual_close_date")
        if actual_close_date:
            payload["actual_close_date"] = {"type": "range", "after": actual_close_date["after"], "before": actual_close_date["before"]}

        actual_start_date = arguments.get("actual_start_date")
        if actual_start_date:
            if 'issue' in type:
                payload["issue"]["actual_start_date"] = {"type": "range", "after": actual_start_date["after"], "before": actual_start_date["before"]}

        created_date = arguments.get("created_date")
        if created_date:
            payload["created_date"] = {"type": "range", "after": created_date["after"], "before": created_date["before"]}

        modified_date = arguments.get("modified_date")
        if modified_date:
            payload["modified_date"] = {"type": "range", "after": modified_date["after"], "before": modified_date["before"]}

        if payload["issue"] == {}:
            payload.pop("issue")

        if payload["ticket"] == {}:
            payload.pop("ticket")

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

        stage = arguments.get("stage")
        if stage:
            payload["stage_v2"] = stage

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
    elif name == "list_parts":
        if not arguments:
            raise ValueError("Missing arguments")

        payload = {}
        payload["enhancement"] = {}

        type = arguments.get("type")
        if not type:
            raise ValueError("Missing type parameter")
        payload["type"] = type
        
        cursor = arguments.get("cursor")
        if cursor:
            payload["cursor"] = cursor["next_cursor"]
            payload["mode"] = cursor["mode"]
        
        owned_by = arguments.get("owned_by")
        if owned_by:
            payload["owned_by"] = owned_by
        
        parent_part = arguments.get("parent_part")
        if parent_part:
            payload["parent_part"] = {"parts": parent_part}
        
        created_by = arguments.get("created_by")
        if created_by:
            payload["created_by"] = created_by
        
        modified_by = arguments.get("modified_by")
        if modified_by:
            payload["modified_by"] = modified_by
        
        sort_by = arguments.get("sort_by")
        if sort_by:
            payload["sort_by"] = sort_by
        
        accounts = arguments.get("accounts")
        if accounts:
            if 'enhancement' in type:
                payload["enhancement"]["accounts"] = accounts
        
        target_close_date = arguments.get("target_close_date")
        if target_close_date:
            if 'enhancement' in type:
                payload["enhancement"]["target_close_date"] = {"after": target_close_date["after"], "before": target_close_date["before"]}
        
        target_start_date = arguments.get("target_start_date")
        if target_start_date:
            if 'enhancement' in type:
                payload["enhancement"]["target_start_date"] = {"after": target_start_date["after"], "before": target_start_date["before"]}

        actual_close_date = arguments.get("actual_close_date")
        if actual_close_date:
            if 'enhancement' in type:
                payload["enhancement"]["actual_close_date"] = {"after": actual_close_date["after"], "before": actual_close_date["before"]}
        
        actual_start_date = arguments.get("actual_start_date")
        if actual_start_date:
            if 'enhancement' in type:
                payload["enhancement"]["actual_start_date"] = {"after": actual_start_date["after"], "before": actual_start_date["before"]}

        if payload["enhancement"] == {}:
            payload.pop("enhancement")

        response = make_devrev_request(
            "parts.list",
            payload
        )
        
        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"List parts failed with status {response.status_code}: {error_text}"
                )
            ]
        
        return [
            types.TextContent(
                type="text",
                text=f"Parts listed successfully: {response.json()}"
            )
        ]
    elif name == "list_meetings":
        if not arguments:
            arguments = {}

        payload = {}
        
        channel = arguments.get("channel")
        if channel:
            payload["channel"] = channel

        created_by = arguments.get("created_by")
        if created_by:
            payload["created_by"] = created_by

        created_date = arguments.get("created_date")
        if created_date:
            payload["created_date"] = {"type": "range", "after": created_date["after"], "before": created_date["before"]}

        cursor = arguments.get("cursor")
        if cursor:
            payload["cursor"] = cursor["next_cursor"]
            payload["mode"] = cursor["mode"]

        ended_date = arguments.get("ended_date")
        if ended_date:
            payload["ended_date"] = {"type": "range", "after": ended_date["after"], "before": ended_date["before"]}

        external_ref = arguments.get("external_ref")
        if external_ref:
            payload["external_ref"] = external_ref

        limit = arguments.get("limit")
        if limit:
            payload["limit"] = limit

        members = arguments.get("members")
        if members:
            payload["members"] = members

        modified_date = arguments.get("modified_date")
        if modified_date:
            payload["modified_date"] = {"type": "range", "after": modified_date["after"], "before": modified_date["before"]}

        organizer = arguments.get("organizer")
        if organizer:
            payload["organizer"] = organizer

        scheduled_date = arguments.get("scheduled_date")
        if scheduled_date:
            payload["scheduled_date"] = {"type": "range", "after": scheduled_date["after"], "before": scheduled_date["before"]}

        sort_by = arguments.get("sort_by")
        if sort_by:
            payload["sort_by"] = sort_by

        state = arguments.get("state")
        if state:
            payload["state"] = state

        response = make_devrev_request(
            "meetings.list",
            payload
        )

        if response.status_code != 200:
            error_text = response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"List meetings failed with status {response.status_code}: {error_text}"
                )
            ]

        return [
            types.TextContent(
                type="text",
                text=f"Meetings listed successfully: {response.json()}"
            )
        ]
    elif name == "valid_stage_transition":
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

        current_stage_id = None
        leaf_type = None
        subtype = None

        if(type == "issue" or type == "ticket"):
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
                        text=f"Get work item failed with status {response.status_code}: {error_text}"
                    )
                ]
            
            current_stage_id = response.json().get("work", {}).get("stage", {}).get("stage", {}).get("id", {})
            leaf_type = response.json().get("work", {}).get("type", {})
            subtype = response.json().get("work", {}).get("subtype", {})

        elif(type == "enhancement"):
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

            current_stage_id = response.json().get("part", {}).get("stage_v2", {}).get("stage", {}).get("id", {})
            leaf_type = response.json().get("part", {}).get("type", {})
            subtype = response.json().get("part", {}).get("subtype", {})
        else:
            raise ValueError("Invalid type parameter")
        
        if(current_stage_id == {} or leaf_type == {}):
            raise ValueError("Could not get current stage or leaf type")
        
        schema_payload = {}
        if(leaf_type != {}):
            schema_payload["leaf_type"] = leaf_type
        if(subtype != {}):
            schema_payload["custom_schema_spec"] = {"subtype": subtype}
        
        schema_response = make_devrev_request(
            "schemas.aggregated.get",
            schema_payload
        )

        if schema_response.status_code != 200:
            error_text = schema_response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Get schema failed with status {schema_response.status_code}: {error_text}"
                )
            ]
        
        stage_diagram_id = schema_response.json().get("schema", {}).get("stage_diagram_id", {}).get("id", {})
        if stage_diagram_id == None:
            raise ValueError("Could not get stage diagram id")
        
        stage_transitions_response = make_devrev_request(
            "stage-diagrams.get",
            {"id": stage_diagram_id}
        )

        if stage_transitions_response.status_code != 200:
            error_text = stage_transitions_response.text
            return [
                types.TextContent(
                    type="text",
                    text=f"Get stage diagram for Get stage transitions failed with status {stage_transitions_response.status_code}: {error_text}"
                )
            ]

        stages = stage_transitions_response.json().get("stage_diagram", {}).get("stages", [])
        for stage in stages:
            if stage.get("stage", {}).get("id") == current_stage_id:
                transitions = stage.get("transitions", [])
                return [
                    types.TextContent(
                        type="text",
                        text=f"Valid Transitions for '{id}' from current stage:\n{transitions}"
                    )
                ]

        return [
            types.TextContent(
                type="text",
                text=f"No valid transitions found for '{id}' from current stage"
            ),
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
