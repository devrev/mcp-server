# DevRev MCP server

## Overview

A Model Context Protocol server for DevRev. It is used to search and retrieve information using the DevRev APIs.

## Tools

### Core Tools

#### `search`
Search for information using the DevRev search API with hybrid search capabilities.

**Description**: Search DevRev objects using hybrid search. Supports natural language queries across tickets, issues, articles, parts, and users. Returns enriched results with metadata, ownership, status, and organizational context for efficient triage and analysis.

**Parameters**:
- `query` (string, required): The search query string
- `namespace` (string, required): The namespace to search in. Must be one of:
  - `article` - Knowledge base articles and documentation
  - `issue` - Internal development issues and bugs
  - `ticket` - Customer support tickets
  - `part` - Product parts and components
  - `dev_user` - DevRev users and team members

**Example Usage**:
```
Search for "login error" in tickets namespace to find customer support tickets
Search for "authentication bug" in issues namespace to find development issues
```

#### `get_object`
Retrieve comprehensive information about any DevRev object.

**Description**: Retrieve comprehensive information about any DevRev object including tickets, issues, parts, and users. Returns complete metadata, relationships, assignment details, and history for thorough analysis and investigation.

**Parameters**:
- `id` (string, required): The DevRev object ID (e.g., "TKT-12345", "ISS-67890")

**Example Usage**:
```
Get details for ticket TKT-12345
Get information about issue ISS-67890
```

#### `create_object`
Create new DevRev tickets or issues with full metadata support.

**Description**: Create new DevRev tickets or issues with full metadata support. Supports both customer-facing tickets and internal issues with proper assignment, categorization, and detailed descriptions for workflow automation.

**Parameters**:
- `type` (string, required): The type of object to create ("issue" or "ticket")
- `title` (string, required): The title/summary of the object
- `applies_to_part` (string, required): The part ID this object applies to
- `body` (string, optional): The body/description of the object
- `owned_by` (array of strings, optional): List of user IDs who should own this object

**Example Usage**:
```
Create a customer ticket for a login issue
Create an internal issue for a bug fix
```

#### `update_object`
Update existing DevRev tickets or issues with new information.

**Description**: Update existing DevRev tickets or issues with new information, descriptions, or titles. Maintains object history and audit trails while allowing incremental updates as investigations progress.

**Parameters**:
- `id` (string, required): The ID of the object to update
- `type` (string, required): The type of object ("issue" or "ticket")
- `title` (string, optional): New title for the object
- `body` (string, optional): New body/description for the object

### Advanced Tools

#### `get_timeline_entries`
Retrieve chronological timeline of all activity on a DevRev ticket.

**Description**: Retrieve chronological timeline of all activity on a DevRev ticket including comments, status changes, assignments, and system events. Essential for understanding ticket progression, customer interactions, and audit trails. Accepts flexible ID formats (TKT-12345, 12345, or full don: format) and provides multiple output formats for different use cases.

**Parameters**:
- `id` (string, required): The ticket ID in various formats (TKT-12345, 12345, etc.)
- `format` (string, optional): Output format ("summary" by default)

#### `get_ticket`
Get a DevRev ticket with all associated timeline entries and artifacts.

**Description**: Get a DevRev ticket with all associated timeline entries and artifacts. Provides enriched ticket data with complete conversation history and attached files for comprehensive support analysis.

**Parameters**:
- `id` (string, required): The ticket ID

#### `download_artifact`
Download a DevRev artifact to a specified directory.

**Description**: Download a DevRev artifact to a specified directory. Retrieves the artifact file and saves it locally with proper metadata.

**Parameters**:
- `artifact_id` (string, required): The artifact ID to download
- `download_directory` (string, required): Local directory path to save the artifact

## Resources

The MCP server provides several resource endpoints for accessing DevRev data through URI-based routing:

### Ticket Resources

- `devrev://tickets/{ticket_id}` - Access comprehensive ticket information with navigation links
- `devrev://tickets/{ticket_id}/timeline` - Access enriched timeline for a ticket with customer context
- `devrev://tickets/{ticket_id}/timeline/{entry_id}` - Access individual timeline entry details
- `devrev://tickets/{ticket_id}/artifacts` - Access all artifacts associated with a ticket

### Artifact Resources

- `devrev://artifacts/{artifact_id}` - Access artifact metadata with download URLs
- `devrev://artifacts/{artifact_id}/tickets` - Get all tickets that reference an artifact

## Configuration

### Get the DevRev API key

1. Go to https://app.devrev.ai/signup and create an account.
2. Import your data from your existing data sources like Salesforce, Zendesk while following the instructions [here](https://devrev.ai/docs/import#available-sources).
3. Generate an access token while following the instructions [here](https://developer.devrev.ai/public/about/authentication#personal-access-token-usage).

### Usage with Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Published Servers Configuration</summary>

```json
"mcpServers": {
  "devrev": {
    "command": "uvx",
    "args": [
      "devrev-mcp"
    ],
    "env": {
      "DEVREV_API_KEY": "YOUR_DEVREV_API_KEY"
    }
  }
}
```

</details>

<details>
  <summary>Development/Unpublished Servers Configuration</summary>

```json
"mcpServers": {
  "devrev": {
    "command": "uv",
    "args": [
      "--directory",
      "Path to src/devrev_mcp directory",
      "run",
      "devrev-mcp"
    ],
    "env": {
      "DEVREV_API_KEY": "YOUR_DEVREV_API_KEY"
    }
  }
}
```

</details>

## Features

- **Hybrid Search**: Advanced search capabilities across all DevRev object types
- **Rich Metadata**: Complete object information including relationships and history
- **Timeline Analysis**: Detailed conversation flows and activity tracking
- **Artifact Management**: File handling with download capabilities
- **Resource Navigation**: URI-based resource access with automatic routing
- **Caching**: Intelligent caching for improved performance
- **Error Handling**: Comprehensive error handling with detailed logging

## Development

This MCP server is built using FastMCP and provides modular tools and resources for DevRev integration. The codebase is organized into:

- `tools/` - Individual tool implementations
- `resources/` - Resource handlers for different object types
- `types.py` - Type definitions and data structures
- `utils.py` - Shared utilities and API helpers
