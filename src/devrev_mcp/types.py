"""
DevRev MCP Server Type Definitions

Contains enums, constants, and type definitions for DevRev objects
to improve model understanding and provide clear documentation.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class TimelineEntryVisibility(Enum):
    """
    Timeline entry visibility levels that control access to entries.
    
    These visibility levels determine who can see timeline entries:
    - PRIVATE: Only visible to the creator of the entry
    - INTERNAL: Visible within the Dev organization only  
    - EXTERNAL: Visible to the Dev organization and Rev users (customers)
    - PUBLIC: Visible to all users (default is EXTERNAL if not specified)
    """
    PRIVATE = "private"
    INTERNAL = "internal" 
    EXTERNAL = "external"
    PUBLIC = "public"

    @classmethod
    def get_description(cls, visibility: str) -> str:
        """Get human-readable description of visibility level."""
        descriptions = {
            cls.PRIVATE.value: "Only visible to the creator",
            cls.INTERNAL.value: "Visible within the Dev organization",  
            cls.EXTERNAL.value: "Visible to Dev organization and Rev users (customers)",
            cls.PUBLIC.value: "Visible to all users"
        }
        return descriptions.get(visibility, f"Unknown visibility: {visibility}")

    @classmethod
    def get_audience(cls, visibility: str) -> str:
        """Get the audience who can see this visibility level."""
        audiences = {
            cls.PRIVATE.value: "Creator only",
            cls.INTERNAL.value: "Dev organization members",
            cls.EXTERNAL.value: "Dev organization + customers", 
            cls.PUBLIC.value: "Everyone"
        }
        return audiences.get(visibility, "Unknown")

    @classmethod
    def is_customer_visible(cls, visibility: str) -> bool:
        """Check if customers can see entries with this visibility."""
        return visibility in [cls.EXTERNAL.value, cls.PUBLIC.value]

    @classmethod
    def is_internal_only(cls, visibility: str) -> bool:
        """Check if entry is restricted to internal users only."""
        return visibility in [cls.PRIVATE.value, cls.INTERNAL.value]


@dataclass
class VisibilityInfo:
    """
    Container for visibility information with helpful context.
    """
    level: str
    description: str
    audience: str
    customer_visible: bool
    internal_only: bool
    
    @classmethod
    def from_visibility(cls, visibility: Optional[str]) -> 'VisibilityInfo':
        """Create VisibilityInfo from a visibility string."""
        # Default to EXTERNAL if not specified
        vis_level = visibility or TimelineEntryVisibility.EXTERNAL.value
        
        return cls(
            level=vis_level,
            description=TimelineEntryVisibility.get_description(vis_level),
            audience=TimelineEntryVisibility.get_audience(vis_level),
            customer_visible=TimelineEntryVisibility.is_customer_visible(vis_level),
            internal_only=TimelineEntryVisibility.is_internal_only(vis_level)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "level": self.level,
            "description": self.description,
            "audience": self.audience,
            "customer_visible": self.customer_visible,
            "internal_only": self.internal_only
        }


class TimelineEntryType(Enum):
    """
    Common timeline entry types in DevRev.
    """
    TIMELINE_COMMENT = "timeline_comment"
    WORK_CREATED = "work_created"
    STAGE_UPDATED = "stage_updated"
    PART_SUGGESTED = "part_suggested"
    WORK_UPDATED = "work_updated"
    
    @classmethod
    def is_conversation_type(cls, entry_type: str) -> bool:
        """Check if this entry type represents a conversation/comment."""
        return entry_type == cls.TIMELINE_COMMENT.value
    
    @classmethod
    def is_system_event(cls, entry_type: str) -> bool:
        """Check if this entry type is a system-generated event."""
        return entry_type in [
            cls.WORK_CREATED.value,
            cls.STAGE_UPDATED.value, 
            cls.PART_SUGGESTED.value,
            cls.WORK_UPDATED.value
        ]


def format_visibility_summary(entries_with_visibility: list) -> Dict[str, Any]:
    """
    Generate a summary of visibility levels across timeline entries.
    
    Args:
        entries_with_visibility: List of timeline entries with visibility info
        
    Returns:
        Dictionary with visibility statistics and breakdown
    """
    visibility_counts = {}
    customer_visible_count = 0
    internal_only_count = 0
    
    for entry in entries_with_visibility:
        visibility = entry.get("visibility_info", {})
        level = visibility.get("level", "external")
        
        visibility_counts[level] = visibility_counts.get(level, 0) + 1
        
        if visibility.get("customer_visible", False):
            customer_visible_count += 1
        if visibility.get("internal_only", False):
            internal_only_count += 1
    
    total_entries = len(entries_with_visibility)
    
    return {
        "total_entries": total_entries,
        "visibility_breakdown": visibility_counts,
        "customer_visible_entries": customer_visible_count,
        "internal_only_entries": internal_only_count,
        "customer_visible_percentage": round((customer_visible_count / total_entries * 100), 1) if total_entries > 0 else 0,
        "internal_only_percentage": round((internal_only_count / total_entries * 100), 1) if total_entries > 0 else 0
    } 