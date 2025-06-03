"""
Copyright (c) 2025 DevRev, Inc.
SPDX-License-Identifier: MIT

This module implements the FastMCP server for DevRev integration.
"""

import json
from typing import Dict, Any

from fastmcp import FastMCP, Context
from mcp import types

# Import modular resources and tools
from .resources.ticket import ticket as ticket_resource
from .resources.timeline import timeline as timeline_resource
from .resources.timeline_entry import timeline_entry as timeline_entry_resource
from .resources.artifact import artifact as artifact_resource
from .resources.ticket_artifacts import ticket_artifacts as ticket_artifacts_resource
from .resources.work import works as work_resource
from .resources.issue import issue as issue_resource
from .tools.get_timeline_entries import get_timeline_entries as get_timeline_entries_tool
from .tools.get_ticket import get_ticket as get_ticket_tool
from .tools.search import search as search_tool
from .tools.create_object import create_object as create_object_tool
from .tools.update_object import update_object as update_object_tool
from .tools.download_artifact import download_artifact as download_artifact_tool
from .tools.get_work import get_work as get_work_tool
from .tools.get_issue import get_issue as get_issue_tool
from .tools.create_timeline_comment import create_timeline_comment as create_timeline_comment_tool

# Import new types for visibility handling
from .types import VisibilityInfo, TimelineEntryType, format_visibility_summary

# Create the FastMCP server
mcp = FastMCP(
    name="devrev_mcp",
    version="0.1.1",
    description="DevRev MCP Server - Provides tools for interacting with DevRev API"
)

# Import cache utility to prevent unbounded memory growth
from .cache import devrev_cache

@mcp.tool(
    name="search",
    description="""Search DevRev objects using hybrid search across multiple content types.

This tool performs intelligent search across DevRev data using natural language queries.
It combines semantic understanding with exact matching to find relevant content.

Supported namespaces:
- article: Search knowledge base articles and documentation
- issue: Search internal issues and bug reports  
- ticket: Search customer support tickets
- part: Search product parts and components
- dev_user: Search team members and user profiles

Usage examples:
- Find tickets about a specific technology: query="python dependency issues", namespace="ticket"
- Search for team expertise: query="frontend react developer", namespace="dev_user"
- Look up documentation: query="API authentication guide", namespace="article"
- Find related issues: query="memory leak in scanner", namespace="issue"

Returns enriched results with metadata, ownership, status, and organizational context
for efficient triage and analysis.""",
    tags=["search", "devrev", "tickets", "issues", "articles", "hybrid-search"]
)
async def search(query: str, namespace: str, ctx: Context) -> str:
    """
    Search DevRev using the provided query and return parsed, useful information.
    
    Args:
        query: The search query string
        namespace: The namespace to search in (article, issue, ticket, part, dev_user)
    
    Returns:
        JSON string containing parsed search results with key information
    """
    return await search_tool(query, namespace, ctx)

@mcp.tool(
    name="create_object",
    description="Create new DevRev tickets or issues with full metadata support. Supports both customer-facing tickets and internal issues with proper assignment, categorization, and detailed descriptions for workflow automation.",
    tags=["create", "devrev", "tickets", "issues", "workflow", "automation"]
)
async def create_object(
    type: str,
    title: str, 
    applies_to_part: str,
    ctx: Context,
    body: str = "",
    owned_by: list[str] | None = None
) -> str:
    """
    Create a new issue or ticket in DevRev.
    
    Args:
        type: The type of object to create ("issue" or "ticket")
        title: The title/summary of the object
        applies_to_part: The part ID this object applies to
        body: The body/description of the object (optional)
        owned_by: List of user IDs who should own this object (optional)
    
    Returns:
        JSON string containing the created object information
    """
    return await create_object_tool(type, title, applies_to_part, ctx, body, owned_by)

@mcp.tool(
    name="update_object", 
    description="Update existing DevRev tickets or issues with new information, descriptions, or titles. Accepts flexible ID formats for tickets/issues. Maintains object history and audit trails while allowing incremental updates as investigations progress.",
    tags=["update", "devrev", "tickets", "issues", "maintenance", "audit"]
)
async def update_object(
    id: str,
    type: str,
    ctx: Context,
    title: str | None = None,
    body: str | None = None
) -> str:
    """
    Update an existing issue or ticket in DevRev.
    
    Args:
        id: The DevRev object ID - for tickets accepts TKT-12345, 12345, or full don:core format; 
            for issues accepts ISS-12345, 12345, or full don:core format
        type: The type of object ("issue" or "ticket")
        title: New title for the object (optional)
        body: New body/description for the object (optional)
    
    Returns:
        JSON string containing the updated object information
    """
    return await update_object_tool(id, type, ctx, devrev_cache, title, body)


# Specialized resource handlers for different DevRev object types

# Resource tag constants
TICKET_RESOURCE_TAGS = ["ticket", "devrev", "customer-support", "navigation"]
TIMELINE_RESOURCE_TAGS = ["timeline", "devrev", "customer-support", "conversation", "visibility", "audit"]
TIMELINE_ENTRY_RESOURCE_TAGS = ["timeline-entry", "devrev", "customer-support", "conversation", "navigation"]
TICKET_ARTIFACTS_RESOURCE_TAGS = ["artifacts", "devrev", "customer-support", "collection", "files", "navigation"]
ARTIFACT_RESOURCE_TAGS = ["artifact", "devrev", "files", "metadata", "download"]
WORK_RESOURCE_TAGS = ["work", "devrev", "unified", "tickets", "issues", "navigation"]
ISSUE_RESOURCE_TAGS = ["issue", "devrev", "internal-work", "navigation"]

@mcp.resource(
    uri="devrev://tickets/{ticket_id}",
    tags=TICKET_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://tickets/TKT-{ticket_number}",
    tags=TICKET_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://tickets/don:core:dvrv-us-1:devo/{dev_org_id}:ticket/{ticket_number}",
    tags=TICKET_RESOURCE_TAGS
)
async def ticket(ctx: Context, ticket_id: str = None, ticket_number: str = None, dev_org_id: str = None) -> str:
    """
    Access comprehensive DevRev ticket information with timeline and artifacts. 
    Supports multiple URI formats: numeric (12345), TKT format (TKT-12345), and full don:core IDs.
    
    Args:
        ticket_id: The DevRev ticket ID (numeric, e.g., 12345)
        ticket_number: The numeric part of the ticket ID (e.g., 12345 for TKT-12345)
        dev_org_id: The dev org ID (e.g., 118WAPdKBc) - unused but required for don:core format
        ctx: FastMCP context
    
    Returns:
        JSON string containing the ticket data with navigation links
    """
    # Normalize to ticket number - all formats end up as the numeric ID
    numeric_id = ticket_id or ticket_number
    return await ticket_resource(numeric_id, ctx, devrev_cache)

@mcp.resource(
    uri="devrev://tickets/{ticket_id}/timeline",
    tags=TIMELINE_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://timeline/{ticket_id}",
    tags=TIMELINE_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://timeline/TKT-{ticket_number}",
    tags=TIMELINE_RESOURCE_TAGS
)
async def ticket_timeline(ctx: Context, ticket_id: str = None, ticket_number: str = None) -> str:
    """
    Access ticket timeline with conversation flow, artifacts, and detailed visibility information. 
    Includes customer context, visual visibility indicators (🔒🏢👥🌐), and comprehensive audit trail.
    
    Args:
        ticket_id: The DevRev ticket ID (numeric, e.g., 12345)
        ticket_number: The numeric part of the ticket ID (e.g., 12345 for TKT-12345)
        ctx: FastMCP context
    
    Returns:
        JSON string containing enriched timeline with customer context and conversation flow
    """
    # Normalize to ticket number
    numeric_id = ticket_id or ticket_number
    return await timeline_resource(numeric_id, ctx, devrev_cache)

@mcp.resource(
    uri="devrev://tickets/{ticket_id}/timeline/{entry_id}",
    tags=TIMELINE_ENTRY_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://tickets/TKT-{ticket_number}/timeline/{entry_id}",
    tags=TIMELINE_ENTRY_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://tickets/don:core:dvrv-us-1:devo/{dev_org_id}:ticket/{ticket_number}/timeline/{entry_id}",
    tags=TIMELINE_ENTRY_RESOURCE_TAGS
)
async def timeline_entry(ctx: Context, ticket_id: str = None, ticket_number: str = None, dev_org_id: str = None, entry_id: str = None) -> str:
    """
    Access individual timeline entry with detailed conversation data and navigation links. 
    Provides specific entry context within ticket timeline.
    
    Args:
        ticket_id: The DevRev ticket ID (numeric, e.g., 12345)
        ticket_number: The numeric part of the ticket ID (e.g., 12345 for TKT-12345)
        dev_org_id: The dev org ID (e.g., 118WAPdKBc) - unused but required for don:core format
        entry_id: The timeline entry ID
        ctx: FastMCP context
    
    Returns:
        JSON string containing the timeline entry data with links
    """
    # Normalize to ticket number
    numeric_id = ticket_id or ticket_number
    
    # Construct full timeline ID if needed
    if not entry_id.startswith("don:core:"):
        # This is a simplified ID, we'll need to fetch it via the ticket timeline
        return await timeline_resource(numeric_id, ctx, devrev_cache)
    
    result = await timeline_entry_resource(entry_id, ctx, devrev_cache)
    
    # Add navigation links
    import json
    entry_data = json.loads(result)
    entry_data["links"] = {
        "ticket": f"devrev://tickets/{numeric_id}",
        "timeline": f"devrev://tickets/{numeric_id}/timeline"
    }
    
    return json.dumps(entry_data, indent=2)

@mcp.resource(
    uri="devrev://tickets/{ticket_id}/artifacts",
    tags=TICKET_ARTIFACTS_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://tickets/TKT-{ticket_number}/artifacts",
    tags=TICKET_ARTIFACTS_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://tickets/don:core:dvrv-us-1:devo/{dev_org_id}:ticket/{ticket_number}/artifacts",
    tags=TICKET_ARTIFACTS_RESOURCE_TAGS
)
async def ticket_artifacts(ctx: Context, ticket_id: str = None, ticket_number: str = None, dev_org_id: str = None) -> str:
    """
    Access all artifacts associated with a specific ticket. Returns collection of files, screenshots, and documents with download links and metadata.
    
    Args:
        ticket_id: The DevRev ticket ID (numeric, e.g., 12345)
        ticket_number: The numeric part of the ticket ID (e.g., 12345 for TKT-12345)
        dev_org_id: The dev org ID (e.g., 118WAPdKBc) - unused but required for don:core format
        ctx: FastMCP context
    
    Returns:
        JSON string containing artifacts with navigation links
    """
    # Normalize to ticket number
    numeric_id = ticket_id or ticket_number
    return await ticket_artifacts_resource(numeric_id, ctx, devrev_cache)

@mcp.resource(
    uri="devrev://artifacts/{artifact_id}",
    tags=ARTIFACT_RESOURCE_TAGS
)
async def artifact(artifact_id: str, ctx: Context) -> str:
    """
    Access DevRev artifact metadata with temporary download URLs. Provides file information, content type, and secure download links.
    
    Args:
        artifact_id: The DevRev artifact ID
    
    Returns:
        JSON string containing the artifact metadata
    """
    result = await artifact_resource(artifact_id, ctx, devrev_cache)
    
    # Return the artifact data directly
    return result

@mcp.resource(
    uri="devrev://works/don:core:dvrv-us-1:devo/{dev_org_id}:{work_type}/{work_number}",
    tags=WORK_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://works/{work_id}",
    tags=WORK_RESOURCE_TAGS
)
async def works(ctx: Context, work_id: str | None = None, work_type: str | None = None, work_number: str | None = None, dev_org_id: str | None = None) -> str:
    """
    Access any DevRev work item with unified interface for tickets, issues, and other work types. Supports display ID formats (TKT-12345, ISS-9031) with navigation links.
    
    Args:
        work_id: The DevRev work ID (e.g., TKT-12345, ISS-9031)
    
    Returns:
        JSON string containing the work item data with navigation links
    """
    if work_id is not None:
        return await work_resource(work_id, ctx, devrev_cache)
    elif work_type is not None and work_number is not None:
        work_id = f"{work_type}-{work_number}"
        return await work_resource(work_id, ctx, devrev_cache)
    else:
        raise ValueError("work_type and work_number are required if work_id is not provided")


@mcp.resource(
    uri="devrev://issues/{issue_number}",
    tags=ISSUE_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://issues/ISS-{issue_number}",
    tags=ISSUE_RESOURCE_TAGS
)
@mcp.resource(
    uri="devrev://issues/don:core:dvrv-us-1:devo/{dev_org_id}:issue/{issue_number}",
    tags=ISSUE_RESOURCE_TAGS
)
async def issue(ctx: Context, issue_number: str = None, dev_org_id: str = None) -> str:
    """
    Access comprehensive DevRev issue information with timeline and artifacts. Supports multiple URI formats: numeric (9031), ISS format (ISS-9031), and full don:core IDs.
    
    Args:
        issue_id: The DevRev issue ID (numeric, e.g., 9031)
        issue_number: The numeric part of the issue ID (e.g., 9031 for ISS-9031)
        dev_org_id: The dev org ID (e.g., 118WAPdKBc) - unused but required for don:core format
        ctx: FastMCP context
    
    Returns:
        JSON string containing the issue data with navigation links
    """
    # Normalize to issue number - all formats end up as the numeric ID
    return await issue_resource(issue_number, ctx, devrev_cache)


@mcp.resource(
    uri="devrev://issues/{issue_id}/timeline",
    tags=["issue-timeline", "devrev", "internal-work", "conversation", "visibility", "audit"]
)
@mcp.resource(
    uri="devrev://issues/ISS-{issue_number}/timeline",
    tags=["issue-timeline", "devrev", "internal-work", "conversation", "visibility", "audit"]
)
async def issue_timeline(ctx: Context, issue_id: str = None, issue_number: str = None) -> str:
    """
    Access issue timeline with conversation flow, artifacts, and detailed visibility information. Includes internal context, visual visibility indicators (🔒🏢👥🌐), and comprehensive audit trail.
    
    Args:
        issue_id: The DevRev issue ID (numeric, e.g., 9031)
        issue_number: The numeric part of the issue ID (e.g., 9031 for ISS-9031)
        ctx: FastMCP context
    
    Returns:
        JSON string containing enriched timeline with internal context and conversation flow
    """
    # Normalize to issue number
    numeric_id = issue_id or issue_number
    
    # Get issue data to extract timeline
    issue_data_str = await issue_resource(numeric_id, ctx, devrev_cache)
    issue_data = json.loads(issue_data_str)
    timeline_entries = issue_data.get("timeline_entries", [])
    
    # Build simplified timeline structure for issues
    result = {
        "issue_id": f"ISS-{numeric_id}",
        "timeline_entries": timeline_entries,
        "total_entries": len(timeline_entries),
        "links": {
            "issue": f"devrev://issues/{numeric_id}",
            "artifacts": f"devrev://issues/{numeric_id}/artifacts"
        }
    }
    
    return json.dumps(result, indent=2)


@mcp.resource(
    uri="devrev://issues/{issue_id}/artifacts",
    tags=["issue-artifacts", "devrev", "internal-work", "collection", "files", "navigation"]
)
@mcp.resource(
    uri="devrev://issues/ISS-{issue_number}/artifacts",
    tags=["issue-artifacts", "devrev", "internal-work", "collection", "files", "navigation"]
)
async def issue_artifacts(ctx: Context, issue_id: str = None, issue_number: str = None) -> str:
    """
    Access all artifacts associated with a specific issue. Returns collection of files, screenshots, and documents with download links and metadata.
    
    Args:
        issue_id: The DevRev issue ID (numeric, e.g., 9031)
        issue_number: The numeric part of the issue ID (e.g., 9031 for ISS-9031)
        ctx: FastMCP context
    
    Returns:
        JSON string containing artifacts with navigation links
    """
    # Normalize to issue number
    numeric_id = issue_id or issue_number
    
    # Get issue data to extract artifacts
    issue_data_str = await issue_resource(numeric_id, ctx, devrev_cache)
    issue_data = json.loads(issue_data_str)
    artifacts = issue_data.get("artifacts", [])
    
    # Add navigation links to each artifact
    for artifact in artifacts:
        artifact_id = artifact.get("id", "").split("/")[-1] if artifact.get("id") else ""
        if artifact_id:
            artifact["links"] = {
                "self": f"devrev://artifacts/{artifact_id}",
                "issue": f"devrev://issues/{numeric_id}"
            }
    
    result = {
        "artifacts": artifacts,
        "total_artifacts": len(artifacts),
        "links": {
            "issue": f"devrev://issues/{numeric_id}",
            "timeline": f"devrev://issues/{numeric_id}/timeline"
        }
    }
    
    return json.dumps(result, indent=2)


@mcp.tool(
    name="get_timeline_entries",
    description="""
    Retrieve chronological timeline of all activity on a DevRev ticket including 
    comments, status changes, assignments, and system events with detailed visibility information.
    
    Essential for understanding ticket progression, customer interactions, and audit trails. 
    Each entry includes:
    - Visibility level (private/internal/external/public) showing who can access it
    - Visual indicators (🔒🏢👥🌐) for quick visibility identification  
    - Percentage breakdown of customer-visible vs internal-only content
    - Audience information (creator only, dev org, dev org + customers, everyone)
    
    Accepts flexible ID formats (TKT-12345, 12345, or full don: format) and provides 
    multiple output formats for different use cases.
    """,
    tags=["timeline", "devrev", "tickets", "history", "conversations", "audit", "visibility"]
)
async def get_timeline_entries(id: str, ctx: Context, format: str = "summary") -> str:
    """
    Get all timeline entries for a DevRev ticket using its ID with flexible formatting.
    
    Args:
        id: The DevRev ticket ID - accepts TKT-12345, 12345, or full don:core format
        format: Output format - "summary" (key info), "detailed" (conversation focus), or "full" (complete data)
    """
    return await get_timeline_entries_tool(id, ctx, format)

@mcp.tool(
    name="get_ticket",
    description="Get a DevRev ticket with all associated timeline entries and artifacts. Provides enriched ticket data with complete conversation history and attached files for comprehensive support analysis.",
    tags=["ticket", "devrev", "enriched", "timeline", "artifacts", "support"]
)
async def get_ticket(id: str, ctx: Context) -> str:
    """
    Get a DevRev ticket with all associated timeline entries and artifacts.
    
    Args:
        id: The DevRev ticket ID - accepts TKT-12345, 12345, or full don:core format
    
    Returns:
        JSON string containing the ticket data with timeline entries and artifacts
    """
    return await get_ticket_tool(id, ctx)

@mcp.tool(
    name="download_artifact",
    description="Download a DevRev artifact to a specified directory using its full artifact ID. Requires the complete don:core artifact ID format (e.g., don:core:dvrv-us-1:devo/123:artifact/456), not just the numeric ID. Retrieves the artifact file and saves it locally with proper metadata.",
    tags=["download", "artifact", "devrev", "files", "local-storage"]
)
async def download_artifact(artifact_id: str, download_directory: str, ctx: Context) -> str:
    """
    Download a DevRev artifact to a specified directory.
    
    Args:
        artifact_id: The full DevRev artifact ID in don:core format (e.g., don:core:dvrv-us-1:devo/123:artifact/456). 
                    The numeric ID alone (e.g., 456) will not work.
        download_directory: The local directory path where the artifact should be saved
    
    Returns:
        JSON string containing download result and file information
    """
    return await download_artifact_tool(artifact_id, download_directory, ctx)

@mcp.tool(
    name="get_work",
    description="Get any DevRev work item (ticket, issue, etc.) by ID. Supports unified access to all work item types using their display IDs like TKT-12345, ISS-9031, etc.",
    tags=["work", "devrev", "tickets", "issues", "unified", "get"]
)
async def get_work(id: str, ctx: Context) -> str:
    """
    Get a DevRev work item by ID.
    
    Args:
        id: The DevRev work ID - accepts TKT-12345, ISS-9031, or any work item format
    
    Returns:
        JSON string containing the work item data
    """
    return await get_work_tool(id, ctx)

@mcp.tool(
    name="get_issue",
    description="Get a DevRev issue by ID. Supports unified access to issue using display IDs like ISS-9031, numeric IDs, or full don:core format.",
    tags=["issue", "devrev", "internal-work", "get"]
)
async def get_issue(id: str, ctx: Context) -> str:
    """
    Get a DevRev issue by ID.
    
    Args:
        id: The DevRev issue ID - accepts ISS-9031, 9031, or full don:core format
    
    Returns:
        JSON string containing the issue data
    """
    return await get_issue_tool(id, ctx)

@mcp.tool(
    name="create_timeline_comment",
    description="""Create an internal timeline comment on a DevRev ticket.
    
Adds a comment to the ticket's timeline that is only visible to internal team members 
for documentation and collaboration purposes.

⚠️ REQUIRES MANUAL REVIEW - This tool modifies ticket data and should always be 
manually approved before execution.""",
    tags=["timeline", "comment", "devrev", "internal", "create", "dangerous"]
)
async def create_timeline_comment(work_id: str, body: str, ctx: Context) -> str:
    """
    Create an internal timeline comment on a DevRev ticket.
    
    Args:
        work_id: The DevRev work ID (e.g., "12345", "TKT-12345", "ISS-12345)
        body: The comment text to add to the timeline
    
    Returns:
        JSON string containing the created timeline entry data
    """
    return await create_timeline_comment_tool(work_id, body, ctx)

@mcp.prompt(
    name="investigate_ticket",
    description="""Systematic DevRev ticket investigation following the established support playbook.

This prompt guides you through a comprehensive 6-step investigation process designed to:
- Thoroughly understand customer issues
- Identify root causes systematically  
- Research similar patterns and solutions
- Document findings with proper timestamps
- Provide actionable resolution paths

The investigation follows verification checkpoints at each step to ensure completeness and accuracy. All findings are documented chronologically for future reference and pattern analysis.""",
    tags=["investigation", "support", "ticket", "playbook", "systematic", "devrev"]
)
async def investigate_ticket(
    ticket_id: str,
    ctx: Context,
    customer_context: str = "",
    priority_level: str = "normal",
    special_notes: str = ""
) -> str:
    """
    Generate a systematic ticket investigation prompt following the support playbook.
    
    Args:
        ticket_id: The DevRev ticket ID to investigate (e.g., TKT-12345, DR-67890)
        customer_context: Additional customer context or background (optional)
        priority_level: Investigation priority (low/normal/high/critical, default: normal)
        special_notes: Any special considerations or constraints (optional)
    
    Returns:
        Formatted investigation prompt with systematic workflow
    """
    from datetime import datetime
    
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build the investigation prompt
    prompt_content = f"""# DevRev Ticket Investigation: {ticket_id}

**Investigation Started:** {current_timestamp}
**Priority Level:** {priority_level.upper()}
**Investigator:** Claude MCP Agent

---

## 🎯 **Investigation Objectives**

- [ ] **STEP 1**: Fetch ticket data and establish investigation structure
- [ ] **STEP 2**: Analyze customer issue and gather complete context  
- [ ] **STEP 3**: Identify affected repository/component
- [ ] **STEP 4**: Research similar issues and patterns
- [ ] **STEP 5**: Review documentation and known solutions
- [ ] **STEP 6**: Set up test environment if reproduction needed

---

## 📋 **STEP 1: Investigation Setup & Data Gathering**

### **Initial Data Collection**
```bash
# Get current investigation timestamp
date '+%Y-%m-%d %H:%M:%S'

# Fetch primary ticket information
get_ticket(id="{ticket_id}")

# Get complete timeline with all communications
get_timeline_entries(id="{ticket_id}", format="detailed")
```

### **Investigation Structure Setup**
- [ ] Create timestamped todo list for systematic tracking
- [ ] Begin investigation log with chronological documentation
- [ ] Note any artifacts or attachments for download

**Customer Context:** {customer_context if customer_context else "To be determined from ticket data"}

**Special Considerations:** {special_notes if special_notes else "None specified"}

---

## 🔍 **STEP 2: Customer Issue Analysis**

### **Required Analysis Points:**
- [ ] **Exact Issue Description**: What specifically is the customer experiencing?
- [ ] **Customer Environment**: What are their technical configuration details?
- [ ] **Impact Assessment**: How is this affecting their workflow?
- [ ] **Timeline Review**: What communications have occurred?
- [ ] **Artifacts Analysis**: Are there logs, screenshots, or files attached?

### **Verification Checkpoint #2:**
- ✅ Have you fully understood the EXACT customer issue?
- ✅ Do you have complete context on their environment/configuration?
- ✅ Have you reviewed ALL timeline entries for full context?

---

## 🗂️ **STEP 3: Repository & Component Identification**

### **Component Mapping:**
- **UI/Web Application Issues** → `/Users/sara/work/fossa/FOSSA/`
- **CLI/Scanning Issues** → `/Users/sara/work/fossa/fossa-cli/`  
- **API/Authentication Issues** → `/Users/sara/work/fossa/FOSSA/`
- **Documentation Issues** → `/Users/sara/work/docs/`

### **Repository Investigation:**
```bash
# Search for related code in identified repository
# Use Glob/Grep tools for targeted searches
# Document specific file paths and line numbers
```

**Verification Checkpoint #3:** Have you correctly identified the repository for investigation?

---

## 🔍 **STEP 4: Similar Issue Research**

### **Pattern Analysis:**
```bash
# Search for similar tickets
search(query="[key issue terms]", namespace="ticket")

# Look for related issues
search(query="[key issue terms]", namespace="issue")
```

### **Analysis Requirements:**
- [ ] Identify tickets with similar symptoms
- [ ] Distinguish surface similarities from root cause similarities  
- [ ] Note key differences between seemingly similar cases
- [ ] Check resolution patterns for similar issues

**Verification Checkpoint #4:** Are you distinguishing between surface and root cause similarities?

---

## 📚 **STEP 5: Documentation & Knowledge Base**

### **Documentation Review:**
```bash
# Check common issues documentation
Read(/Users/sara/work/docs/common-issues.md)

# Search for issue-specific documentation  
Grep(pattern="[issue-specific-terms]", path="/Users/sara/work/docs/", include="*.md")
```

### **Knowledge Assembly:**
- [ ] Review known workarounds and solutions
- [ ] Check architectural documentation if relevant
- [ ] Identify any edge cases or special configurations
- [ ] Gather relevant technical background

**Verification Checkpoint #5:** Have you checked ALL relevant documentation and considered edge cases?

---

## 🧪 **STEP 6: Test Environment Setup (If Needed)**

### **Environment Preparation:**
If reproduction is required:

```bash
# Create ticket-specific directory
mkdir -p tickets/{ticket_id}
cd tickets/{ticket_id}

# Configure .fossa.yml with correct project ID
cat > .fossa.yml << EOF
version: 3

project:
   id: {ticket_id}
EOF
```

### **Setup Verification:**
- [ ] Directory created with exact ticket ID
- [ ] Configuration file properly set up
- [ ] Test isolation properly established
- [ ] All setup steps documented

**Verification Checkpoint #6:** Is your test directory correct, config accurate, and setup documented?

---

## 📝 **Investigation Documentation Requirements**

### **Continuous Logging:**
- Update investigation file at EVERY step with timestamps
- Document all tool usage and results
- Record verification checkpoint completions
- Note any deviations from standard workflow

### **Final Documentation:**
- [ ] Complete investigation summary
- [ ] Root cause identification (if found)
- [ ] Resolution recommendations
- [ ] Escalation path (if needed)
- [ ] Pattern analysis for future reference

---

## ⚡ **Priority-Specific Guidelines**

**Current Priority: {priority_level.upper()}**

"""

    # Add priority-specific guidance
    if priority_level.lower() == "critical":
        prompt_content += """
### **CRITICAL PRIORITY ACTIONS:**
- Immediately notify relevant teams after initial analysis
- Document customer impact in business terms
- Prepare interim updates for customer communication
- Consider immediate workaround identification
- Escalate to engineering if root cause requires code changes

"""
    elif priority_level.lower() == "high":
        prompt_content += """
### **HIGH PRIORITY ACTIONS:**
- Complete investigation within current session
- Prepare detailed customer communication
- Identify workarounds if available
- Document for pattern tracking

"""

    prompt_content += """
---

## 🚀 **Next Steps**

1. **Begin with STEP 1** - Execute the data gathering commands above
2. **Follow each verification checkpoint** systematically  
3. **Document all findings** with timestamps in investigation file
4. **Complete all steps** before providing recommendations
5. **Prepare final summary** with actionable next steps

**Remember:** This investigation follows the established support playbook for consistency and thoroughness. Each step builds on the previous to ensure no critical information is missed.

---

*Generated by DevRev MCP Investigation Prompt v1.0*
"""

    return prompt_content


def main():
    """Main entry point for the DevRev MCP server."""
    # Run the server
    mcp.run()

if __name__ == "__main__":
    main()