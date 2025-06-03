"""
DevRev Get Timeline Entries Tool

Provides a tool for fetching timeline entries for DevRev tickets with flexible formatting.
"""

import json
from fastmcp import Context
from ..types import VisibilityInfo, TimelineEntryType
from ..error_handler import tool_error_handler
from ..utils import read_resource_content


@tool_error_handler("get_timeline_entries")
async def get_timeline_entries(
    id: str, 
    ctx: Context, 
    format: str = "summary"
) -> str:
    """
    Get timeline entries for a DevRev work item (ticket or issue) with flexible formatting options.
    
    Args:
        id: The DevRev work ID - accepts TKT-12345, ISS-9031, numeric IDs, or full don:core format
        ctx: FastMCP context
        format: Output format - "summary" (key info), "detailed" (conversation focus), or "full" (complete data)
    
    Returns:
        Formatted timeline entries based on the requested format
    """
    # Input validation
    if not id or not id.strip():
        raise ValueError("ID parameter is required and cannot be empty")
    
    if format not in ["summary", "detailed", "full"]:
        raise ValueError(f"Invalid format '{format}'. Must be one of: summary, detailed, full")
    
    try:
        await ctx.info(f"Fetching timeline entries for {id} in {format} format")
        
        # Try different resource URIs and let pattern matching handle the ID format
        resource_uris = [
            f"devrev://tickets/{id}/timeline",
            f"devrev://issues/{id}/timeline"
        ]
        
        timeline_data = None
        for resource_uri in resource_uris:
            try:
                timeline_data = await _read_timeline_data_with_fallback(ctx, resource_uri, id, format)
                if timeline_data and not isinstance(timeline_data, str):  # Found valid data
                    break
            except Exception:
                continue  # Try next URI
        
        if not timeline_data:
            return f"No timeline entries found for {id}"
        if isinstance(timeline_data, str):  # Error message returned
            return timeline_data
        
        
        # Format based on requested type
        if format == "summary":
            return _format_summary(timeline_data, id)
        elif format == "detailed":
            return _format_detailed(timeline_data, id)
        else:  # format == "full"
            try:
                return json.dumps(timeline_data, indent=2, default=str)
            except (TypeError, ValueError) as e:
                await ctx.error(f"Could not serialize timeline data to JSON: {str(e)}")
                return str(timeline_data)
            
    except Exception as e:
        await ctx.error(f"Failed to get timeline entries for {id}: {str(e)}")
        return f"Failed to get timeline entries for work item {id}: {str(e)}"




def _format_summary(timeline_data, display_id: str) -> str:
    """
    Format timeline data as a concise summary focusing on key metrics and latest activity.
    """
    # Handle both dict and list formats
    if isinstance(timeline_data, list):
        conversation = timeline_data
        summary = {}
    else:
        summary = timeline_data.get("summary", {})
        conversation = timeline_data.get("conversation_thread", [])
    
    lines = []
    lines.extend(_build_summary_header(display_id, summary))
    lines.extend(_build_activity_counts(conversation))
    lines.extend(_build_visibility_summary(timeline_data))
    lines.extend(_build_last_activity(summary))
    lines.extend(_build_recent_messages(conversation))
    lines.extend(_build_artifacts_info(timeline_data))
    
    return "\n".join(lines)


def _format_detailed(timeline_data, display_id: str) -> str:
    """
    Format timeline data with focus on conversation flow and key events.
    """
    # Handle both dict and list formats
    if isinstance(timeline_data, list):
        # If it's a list, treat it as the conversation thread
        conversation = timeline_data
        summary = {}
    else:
        # If it's a dict, extract the expected fields
        summary = timeline_data.get("summary", {})
        conversation = timeline_data.get("conversation_thread", [])
    
    lines = [
        f"**{display_id} Detailed Timeline:**",
        "",
        f"**Subject:** {summary.get('subject', 'Unknown')}",
        f"**Status:** {summary.get('current_stage', 'Unknown')}",
        f"**Customer:** {summary.get('customer', 'Unknown')}",
        "",
        "**Conversation Thread:**"
    ]
    
    # Add each conversation entry with visibility information
    for msg in conversation:
        speaker = msg.get("speaker", {})
        timestamp = msg.get("timestamp", "")
        message = msg.get("message", "")
        artifacts = msg.get("artifacts", [])
        visibility_info = msg.get("visibility_info", {})
        
        # Format timestamp to be more readable
        display_time = timestamp[:19].replace("T", " ") if timestamp else "Unknown time"
        
        # Format visibility info
        visibility_text = ""
        if visibility_info:
            level = visibility_info.get("level", "external")
            description = visibility_info.get("description", "")
            audience = visibility_info.get("audience", "")
            
            # Add visibility indicator
            if level == "private":
                visibility_text = " 🔒 [PRIVATE - Creator only]"
            elif level == "internal":
                visibility_text = " 🏢 [INTERNAL - Dev org only]"
            elif level == "external":
                visibility_text = " 👥 [EXTERNAL - Dev org + customers]"
            elif level == "public":
                visibility_text = " 🌐 [PUBLIC - Everyone]"
        
        lines.extend([
            "",
            (f"**{msg.get('seq', '?')}. {speaker.get('name', 'Unknown')} "
             f"({speaker.get('type', 'unknown')}) - {display_time}**{visibility_text}")
        ])
        
        # Add message content with proper formatting
        if message:
            # Handle multi-line messages by indenting them
            message_lines = message.split("\n")
            for line in message_lines:
                if line.strip():
                    lines.append(f"   {line}")
                else:
                    lines.append("")
        
        # Add artifacts info
        if artifacts:
            lines.append(f"   *Attachments: {len(artifacts)} file(s)*")
        
        # Add visibility details if relevant
        if visibility_info and visibility_info.get("level") in ["private", "internal"]:
            lines.append(f"   *Visibility: {visibility_info.get('description', 'Unknown')}*")
    
    # Add key events summary with visibility
    if isinstance(timeline_data, dict):
        key_events = timeline_data.get("key_events", [])
        if key_events:
            lines.extend([
                "",
                "**Key Events:**"
            ])
            for event in key_events[-5:]:  # Show last 5 events
                event_time = event.get("timestamp", "")[:19].replace("T", " ")
                event_type = event.get("type", "unknown")
                actor = event.get("actor", {}).get("name", "System")
                
                # Add visibility indicator for events
                visibility_info = event.get("visibility_info", {})
                visibility_indicator = ""
                if visibility_info:
                    level = visibility_info.get("level", "external")
                    if level == "private":
                        visibility_indicator = " 🔒"
                    elif level == "internal":
                        visibility_indicator = " 🏢"
                    elif level == "external":
                        visibility_indicator = " 👥"
                    elif level == "public":
                        visibility_indicator = " 🌐"
                
                lines.append(f"- {event_time}: {event_type} by {actor}{visibility_indicator}")
        
        # Add overall visibility summary
        if "visibility_summary" in timeline_data:
            vis_summary = timeline_data["visibility_summary"]
            lines.extend([
                "",
                "**Visibility Overview:**",
                f"- Total entries: {vis_summary.get('total_entries', 0)}",
                (f"- Customer-visible: {vis_summary.get('customer_visible_entries', 0)} "
                 f"({vis_summary.get('customer_visible_percentage', 0)}%)"),
                (f"- Internal-only: {vis_summary.get('internal_only_entries', 0)} "
                 f"({vis_summary.get('internal_only_percentage', 0)}%)")
            ])
    
    return "\n".join(lines)


async def _read_timeline_data_with_fallback(ctx, resource_uri: str, display_id: str, format: str):
    """
    Read timeline data with fallback to raw content if JSON parsing fails.
    
    Returns:
        Timeline data dict/list or error message string
    """
    try:
        # Try to read as JSON first
        timeline_data = await read_resource_content(
            ctx, 
            resource_uri, 
            parse_json=True, 
            require_content=False
        )
        
        if not timeline_data:
            return f"No timeline entries found for {display_id}"
        
        return timeline_data
            
    except Exception as resource_error:
        await ctx.error(f"Error reading resource {resource_uri}: {str(resource_error)}")
        
        # Fallback: try reading as raw content
        try:
            timeline_data = await read_resource_content(
                ctx, 
                resource_uri, 
                parse_json=False, 
                require_content=False
            )
            if format == "full" and timeline_data:
                return str(timeline_data)
            else:
                return f"Error: Could not parse timeline data for {display_id}"
        except Exception:
            raise resource_error


def _build_summary_header(display_id: str, summary: dict) -> list:
    """Build the header section of the summary."""
    return [
        f"**{display_id} Timeline Summary:**",
        "",
        f"**Subject:** {summary.get('subject', 'Unknown')}",
        f"**Status:** {summary.get('current_stage', 'Unknown')}",
        f"**Customer:** {summary.get('customer', 'Unknown')}",
        f"**Created:** {summary.get('created_date', 'Unknown')}",
    ]


def _build_activity_counts(conversation: list) -> list:
    """Build activity counts section."""
    customer_messages = [msg for msg in conversation if msg.get("speaker", {}).get("type") == "customer"]
    support_messages = [msg for msg in conversation if msg.get("speaker", {}).get("type") == "support"]
    
    return [
        "",
        (f"**Activity:** {len(customer_messages)} customer messages, "
         f"{len(support_messages)} support responses"),
    ]


def _build_visibility_summary(timeline_data) -> list:
    """Build visibility summary section."""
    lines = []
    if isinstance(timeline_data, dict) and "visibility_summary" in timeline_data:
        vis_summary = timeline_data["visibility_summary"]
        lines.extend([
            "",
            "**Visibility Summary:**",
            (f"- Customer-visible entries: {vis_summary.get('customer_visible_entries', 0)} "
             f"({vis_summary.get('customer_visible_percentage', 0)}%)"),
            (f"- Internal-only entries: {vis_summary.get('internal_only_entries', 0)} "
             f"({vis_summary.get('internal_only_percentage', 0)}%)"),
        ])
    return lines


def _build_last_activity(summary: dict) -> list:
    """Build last activity timestamps section."""
    lines = []
    if summary.get("last_customer_message"):
        lines.append(f"**Last customer message:** {summary['last_customer_message']}")
    if summary.get("last_support_response"):
        lines.append(f"**Last support response:** {summary['last_support_response']}")
    return lines


def _build_recent_messages(conversation: list) -> list:
    """Build recent messages section."""
    lines = []
    if conversation:
        lines.extend([
            "",
            "**Recent Activity:**"
        ])
        
        recent_messages = conversation[-3:] if len(conversation) > 3 else conversation
        for msg in recent_messages:
            speaker = msg.get("speaker", {})
            timestamp = msg.get("timestamp", "")
            timestamp = timestamp[:10] if len(timestamp) >= 10 else timestamp
            message_preview = (msg.get("message", "")[:100] + 
                             ("..." if len(msg.get("message", "")) > 100 else ""))
            
            visibility_indicator = _get_visibility_indicator(msg.get("visibility_info", {}))
            
            lines.append(
                f"- **{speaker.get('name', 'Unknown')}** ({timestamp}): "
                f"{visibility_indicator}{message_preview}"
            )
    return lines


def _build_artifacts_info(timeline_data) -> list:
    """Build artifacts information section."""
    lines = []
    if isinstance(timeline_data, dict):
        artifacts = timeline_data.get("all_artifacts", [])
        if artifacts:
            lines.extend([
                "",
                f"**Attachments:** {len(artifacts)} file(s) attached"
            ])
    return lines


def _get_visibility_indicator(visibility_info: dict) -> str:
    """Get visibility indicator emoji for a message."""
    if not visibility_info:
        return ""
    
    level = visibility_info.get("level", "external")
    indicators = {
        "private": "🔒 ",
        "internal": "🏢 ",
        "external": "👥 ",
        "public": "🌐 "
    }
    return indicators.get(level, "")