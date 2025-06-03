# DevRev MCP Resources

This directory contains resource handlers that provide URI-based access to DevRev data through the Model Context Protocol (MCP). Resources allow you to access DevRev objects using structured URIs and receive enriched data with navigation links and related information.

## Overview

Resources in this MCP server provide specialized access to different types of DevRev objects. Unlike tools which perform actions, resources provide read-only access to data through URI patterns. Each resource handler enriches the data with additional context, navigation links, and related objects.

## Available Resources

### Ticket Resources

#### `ticket.py` - Individual Ticket Access
**URI Pattern**: `devrev://tickets/{ticket_id}`

**Description**: Access comprehensive DevRev ticket information with navigation links to related resources. Includes customer details, status progression, assignment history, and navigation to timeline and artifacts.

**Features**:
- Complete ticket metadata (title, status, severity, stage)
- Customer and organization information
- Owner and assignment details
- Timeline entries with conversation history
- Associated artifacts (files, screenshots, attachments)
- Navigation links to related resources
- Intelligent caching for performance

**Example URIs**:
- `devrev://tickets/12345` - Access ticket TKT-12345
- `devrev://tickets/TKT-67890` - Access ticket using full ID format

**Returned Data Structure**:
```json
{
  "id": "TKT-12345",
  "title": "Customer login issue",
  "severity": "high",
  "stage": { "name": "in_progress" },
  "owned_by": [{"name": "John Doe", "email": "john@example.com"}],
  "rev_org": {"display_name": "Acme Corp"},
  "timeline_entries": [...],
  "artifacts": [...],
  "links": {
    "timeline": "devrev://tickets/12345/timeline",
    "artifacts": "devrev://tickets/12345/artifacts"
  }
}
```

#### Ticket Timeline Access
**URI Pattern**: `devrev://tickets/{ticket_id}/timeline`

**Description**: Access enriched timeline for a ticket with customer context, conversation flow, and artifacts. Returns token-efficient structured format focusing on support workflow.

**Features**:
- Chronological conversation flow
- Customer and agent interactions
- Status change history
- Artifact references within conversations
- Support workflow context
- Customer journey tracking

#### Individual Timeline Entry
**URI Pattern**: `devrev://tickets/{ticket_id}/timeline/{entry_id}`

**Description**: Access individual timeline entry with detailed conversation data and navigation links.

**Features**:
- Detailed entry metadata
- Author information
- Entry type and content
- Associated artifacts
- Navigation to related entries

#### Ticket Artifacts Collection
**URI Pattern**: `devrev://tickets/{ticket_id}/artifacts`

**Description**: Access all artifacts associated with a specific ticket. Returns list of files, screenshots, and documents attached to the ticket.

**Features**:
- Complete artifact listing
- File metadata (size, type, name)
- Upload timestamps and authors
- Download URLs (temporary)
- Reverse links to timeline entries

### Artifact Resources

#### `artifact.py` - Individual Artifact Access
**URI Pattern**: `devrev://artifacts/{artifact_id}`

**Description**: Access DevRev artifact metadata with temporary download URLs and reverse links to associated tickets.

**Features**:
- Complete artifact metadata
- File information (name, size, MIME type)
- Temporary download URLs
- Upload information (author, timestamp)
- Reverse links to associated tickets
- Content analysis metadata

**Example Data Structure**:
```json
{
  "id": "artifact_123",
  "filename": "screenshot.png",
  "size": 1024000,
  "mime_type": "image/png",
  "uploaded_by": {"name": "Customer Support"},
  "created_date": "2024-01-15T10:30:00Z",
  "download_url": "https://...",
  "associated_tickets": ["TKT-12345"],
  "links": {
    "tickets": "devrev://artifacts/artifact_123/tickets"
  }
}
```

#### Artifact Reverse Links
**URI Pattern**: `devrev://artifacts/{artifact_id}/tickets`

**Description**: Access all tickets that reference this artifact. Provides reverse lookup from artifacts to tickets.

**Features**:
- Complete ticket list referencing the artifact
- Ticket metadata and status
- Timeline entry references
- Support workflow context

### Timeline Entry Resources

#### `timeline_entry.py` - Individual Entry Access
**URI Pattern**: Various patterns through timeline access

**Description**: Provides specialized handling for individual timeline entries with rich conversation context.

**Features**:
- Entry type classification (comment, status_change, system_event)
- Author and participant information
- Content formatting and rendering
- Associated artifacts and attachments
- Conversation threading
- Support workflow context

## Resource Implementation Details

### Caching Strategy

All resources implement intelligent caching to improve performance:
- **Cache Keys**: Structured as `{resource_type}:{object_id}`
- **Cache Duration**: Configurable per resource type
- **Cache Invalidation**: Automatic on object updates
- **Memory Management**: LRU eviction for memory efficiency

### Error Handling

Resources provide comprehensive error handling:
- **Not Found**: Returns structured error with suggestions
- **Permission Denied**: Clear error messages with context
- **API Failures**: Graceful degradation with partial data
- **Network Issues**: Retry logic with exponential backoff

### Navigation Links

Resources include navigation links to related objects:
- **Hierarchical Navigation**: Parent-child relationships
- **Cross-References**: Related tickets, artifacts, users
- **Timeline Navigation**: Previous/next entries
- **Search Context**: Back to search results

### Data Enrichment

Each resource enriches basic DevRev data:
- **Relationship Resolution**: Loads related objects
- **Computed Fields**: Derived values and summaries
- **Context Addition**: Workflow and business context
- **Format Optimization**: Token-efficient representations

## Usage Examples

### Accessing a Ticket with Full Context
```
Resource: devrev://tickets/12345
Returns: Complete ticket with timeline, artifacts, and navigation
```

### Following Timeline Conversations
```
1. Start: devrev://tickets/12345/timeline
2. Navigate: devrev://tickets/12345/timeline/entry_456
3. Related: devrev://artifacts/artifact_789
```

### Reverse Artifact Lookup
```
1. Artifact: devrev://artifacts/screenshot_123
2. Related Tickets: devrev://artifacts/screenshot_123/tickets
3. Specific Ticket: devrev://tickets/12345
```

## Development Guidelines

### Adding New Resources

1. Create resource handler in appropriate module
2. Implement URI pattern matching
3. Add data enrichment logic
4. Include navigation links
5. Implement caching strategy
6. Add comprehensive error handling
7. Update this documentation

### Resource Handler Pattern

```python
async def resource_handler(object_id: str, ctx: Context, cache: dict) -> str:
    """
    Standard resource handler pattern.
    
    Args:
        object_id: The object identifier
        ctx: FastMCP context for logging
        cache: Shared cache dictionary
    
    Returns:
        JSON string with enriched object data
    """
    # 1. Normalize and validate object_id
    # 2. Check cache for existing data
    # 3. Fetch from DevRev API
    # 4. Enrich with related data
    # 5. Add navigation links
    # 6. Cache and return result
```

### Testing Resources

Resources should be tested for:
- **URI Pattern Matching**: Correct routing
- **Data Enrichment**: Complete related data
- **Navigation Links**: Valid URIs
- **Error Scenarios**: Graceful failures
- **Performance**: Caching effectiveness
- **Memory Usage**: Resource cleanup

## Performance Considerations

- **Lazy Loading**: Only fetch required related data
- **Batch Operations**: Group API calls when possible
- **Cache Warming**: Pre-load frequently accessed objects
- **Memory Limits**: Implement cache size limits
- **Network Optimization**: Minimize API round trips 