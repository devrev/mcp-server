# DevRev MCP Server

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![DevRev](https://img.shields.io/badge/DevRev-MCP%20Server-orange.svg)](https://devrev.ai)

## Overview

A powerful Model Context Protocol (MCP) server for DevRev that provides comprehensive access to DevRev's APIs. This server enables seamless integration with DevRev's work management system, allowing you to manage work items (issues, tickets), parts (enhancements), meetings, workflow transitions, timeline entries, and sprint planning through natural language interactions.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- A DevRev account with API access
- `uv` or `uvx` (recommended) for package management

### Installation

**Option 1: Using uvx (Recommended)**

```bash
uvx devrev-mcp
```

**Option 2: Using uv**

```bash
uv tool install devrev-mcp
```

**Option 3: Using pip**

```bash
pip install devrev-mcp
```

### Configuration

1. **Get your DevRev API Key**

   - Go to [DevRev Signup](https://app.devrev.ai/signup) and create an account
   - Generate a Personal Access Token following the [authentication guide](https://developer.devrev.ai/public/about/authentication#personal-access-token-usage)

2. **Configure Claude Desktop**

   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "devrev": {
         "command": "uvx",
         "args": ["devrev-mcp"],
         "env": {
           "DEVREV_API_KEY": "YOUR_DEVREV_API_KEY"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** to load the configuration

## 📚 API Documentation

### Search & Discovery

#### `search`

Search across different DevRev namespaces using hybrid search capabilities.

**Parameters:**

- `query` (string, required): Search query
- `namespace` (string, required): One of: `article`, `issue`, `ticket`, `part`, `dev_user`, `account`, `rev_org`

**Example:**

```javascript
{
  "query": "authentication issues",
  "namespace": "issue"
}
```

#### `get_current_user`

Fetch details about the currently authenticated DevRev user.

**Parameters:** None

**Use case:** When user mentions "me" or needs current user context

### Work Items Management

#### `get_work`

Retrieve comprehensive information about a specific work item.

**Parameters:**

- `id` (string, required): DevRev ID of the work item

**Example:**

```javascript
{
  "id": "ISS-123"
}
```

#### `create_work`

Create a new issue or ticket in DevRev.

**Parameters:**

- `type` (string, required): `"issue"` or `"ticket"`
- `title` (string, required): Title of the work item
- `applies_to_part` (string, required): DevRev ID of the part
- `body` (string, optional): Description/body content
- `owned_by` (array, optional): Array of user DevRev IDs

**Example:**

```javascript
{
  "type": "issue",
  "title": "Authentication timeout on login",
  "body": "Users are experiencing timeout errors during login process",
  "applies_to_part": "PROD-456",
  "owned_by": ["DEV-789"]
}
```

#### `update_work`

Update an existing work item.

**Parameters:**

- `id` (string, required): DevRev ID of the work item
- `type` (string, required): `"issue"` or `"ticket"`
- `title` (string, optional): New title
- `body` (string, optional): New body content
- `applies_to_part` (string, optional): New part ID
- `owned_by` (array, optional): New assignees
- `stage` (string, optional): New stage name (use `valid_stage_transition` first)
- `sprint` (string, optional): Sprint ID for issues

**Example:**

```javascript
{
  "id": "ISS-123",
  "type": "issue",
  "stage": "in_progress",
  "owned_by": ["DEV-789", "DEV-101"]
}
```

#### `list_works`

List and filter work items with advanced filtering options.

**Parameters:**

- `type` (array, required): Array of work types: `["issue"]`, `["ticket"]`, or `["issue", "ticket"]`
- `cursor` (object, optional): Pagination cursor with `next_cursor` and `mode`
- `applies_to_part` (array, optional): Filter by part IDs
- `owned_by` (array, optional): Filter by assignee IDs
- `state` (array, optional): Filter by state: `["open", "closed", "in_progress"]`
- `created_date` (object, optional): Date range with `after` and `before`
- `sort_by` (array, optional): Sort order (e.g., `["created_date:desc"]`)

**Example:**

```javascript
{
  "type": ["issue"],
  "state": ["open"],
  "created_date": {
    "after": "2025-01-01T00:00:00Z",
    "before": "2025-01-31T23:59:59Z"
  },
  "sort_by": ["created_date:desc"]
}
```

### Parts Management

#### `get_part`

Retrieve information about a specific part (enhancement).

**Parameters:**

- `id` (string, required): DevRev ID of the part

#### `create_part`

Create a new part (enhancement).

**Parameters:**

- `type` (string, required): `"enhancement"`
- `name` (string, required): Name of the part
- `owned_by` (array, required): Array of user DevRev IDs
- `parent_part` (array, required): Array of parent part IDs
- `description` (string, optional): Part description

#### `update_part`

Update an existing part.

**Parameters:**

- `id` (string, required): DevRev ID of the part
- `type` (string, required): `"enhancement"`
- `name` (string, optional): New name
- `owned_by` (array, optional): New assignees
- `description` (string, optional): New description
- `target_start_date` (string, optional): Target start date (ISO format)
- `target_close_date` (string, optional): Target close date (ISO format)
- `stage` (string, optional): New stage ID

#### `list_parts`

List and filter parts with advanced filtering options.

**Parameters:**

- `type` (string, required): `"enhancement"`
- `cursor` (object, optional): Pagination cursor
- `owned_by` (array, optional): Filter by assignee IDs
- `parent_part` (array, optional): Filter by parent part IDs
- `created_date` (object, optional): Date range filter
- `sort_by` (array, optional): Sort order

### Meetings Management

#### `list_meetings`

List and filter meetings in DevRev.

**Parameters:**

- `channel` (array, optional): Meeting channels: `["amazon_connect", "google_meet", "offline", "other", "teams", "zoom"]`
- `state` (array, optional): Meeting states: `["cancelled", "completed", "no_show", "ongoing", "rejected", "scheduled", "rescheduled", "waiting"]`
- `created_date` (object, optional): Date range filter
- `cursor` (object, optional): Pagination cursor

### Workflow Management

#### `valid_stage_transition`

Get valid stage transitions for a work item or part.

**Parameters:**

- `type` (string, required): `"issue"`, `"ticket"`, or `"enhancement"`
- `id` (string, required): DevRev ID of the item

**Usage:** Always call this before updating stages to ensure valid transitions.

#### `add_timeline_entry`

Add a timeline entry to track updates and progress.

**Parameters:**

- `id` (string, required): DevRev ID of the work item or part
- `timeline_entry` (string, required): Timeline entry content

#### `get_sprints`

Get active or planned sprints for a part.

**Parameters:**

- `ancestor_part_id` (string, required): ID of the part
- `state` (string, optional): `"active"` or `"planned"` (defaults to "active")

## 💡 Usage Examples

### Example 1: Search for Authentication Issues

```
Search for all issues related to authentication problems:
- Query: "authentication login timeout"
- Namespace: "issue"
```

### Example 2: Create and Track a Support Ticket

```
1. Create a ticket for a customer issue
2. Assign it to support team
3. Add timeline entries for progress tracking
4. Update status as work progresses
```

### Example 3: Sprint Planning Workflow

```
1. List all open issues for a specific part
2. Get active sprints for the part
3. Assign issues to appropriate sprint
4. Track progress with timeline entries
```

### Example 4: Issue Analysis and Reporting

```
1. List all issues created in the last month
2. Filter by specific parts or assignees
3. Analyze patterns and common problems
4. Generate reports on issue resolution times
```

## 🛠️ Advanced Configuration

### Environment Variables

| Variable         | Description         | Required | Default |
| ---------------- | ------------------- | -------- | ------- |
| `DEVREV_API_KEY` | Your DevRev API key | Yes      | -       |

### Development Setup

For development or local testing:

```json
{
  "mcpServers": {
    "devrev": {
      "command": "uv",
      "args": ["--directory", "/path/to/devrev-mcp", "run", "devrev-mcp"],
      "env": {
        "DEVREV_API_KEY": "YOUR_DEVREV_API_KEY"
      }
    }
  }
}
```

### Performance Optimization

- **Pagination**: Use cursor-based pagination for large result sets
- **Filtering**: Apply specific filters to reduce API calls
- **Caching**: Consider caching frequently accessed data
- **Batch Operations**: Group related operations when possible

## 🔧 Troubleshooting

### Common Issues

#### Authentication Errors

**Problem:** `Get current user failed with status 401`
**Solution:**

- Verify your API key is correctly set in environment variables
- Check that the API key hasn't expired
- Ensure the key has proper permissions

#### Invalid Part ID Errors

**Problem:** `Create object failed with status 400: Invalid applies_to_part`
**Solution:**

- Use the `search` tool with `namespace: "part"` to find valid part IDs
- Verify the part exists and you have access to it
- Check if the part ID format is correct (e.g., "PROD-123")

#### Stage Transition Errors

**Problem:** `Update object failed with status 400: Invalid stage transition`
**Solution:**

- Always use `valid_stage_transition` before updating stages
- Check current stage and available transitions
- Ensure you have permissions to perform the transition

#### Network Connectivity Issues

**Problem:** Connection timeouts or network errors
**Solution:**

- Check your internet connection
- Verify DevRev API endpoint is accessible
- Consider firewall or proxy settings

#### Invalid Parameter Format

**Problem:** `Missing required parameter` or `Invalid parameter format`
**Solution:**

- Check parameter names and types in the API documentation
- Ensure required parameters are provided
- Verify date formats use ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ)

### Debugging Tips

1. **Enable verbose logging** in your MCP client
2. **Check API responses** for detailed error messages
3. **Use search tools** to explore available resources
4. **Test with simple operations** first before complex workflows
5. **Verify permissions** for the operations you're trying to perform

### Getting Help

- **Documentation**: [DevRev API Documentation](https://developer.devrev.ai)
- **Support**: Contact DevRev support for API-related issues
- **Community**: Join DevRev community for discussions and tips

## 🏗️ Architecture

### Core Components

- **Server**: MCP server implementation with tool definitions
- **Utils**: Utility functions for API communication
- **Tools**: Individual tool implementations with proper error handling

### API Integration

The server integrates with DevRev's REST API using:

- **Authentication**: Bearer token authentication
- **Endpoints**: RESTful API endpoints for different resources
- **Error Handling**: Comprehensive error handling and reporting
- **Pagination**: Cursor-based pagination for large datasets

## 📋 Features

- **🔍 Comprehensive Search**: Search across multiple namespaces with hybrid capabilities
- **📝 Work Item Management**: Full CRUD operations for issues and tickets
- **🧩 Part Management**: Complete part lifecycle management
- **👥 User Management**: Access to user information and context
- **📅 Meeting Integration**: Meeting listing and filtering
- **🔄 Workflow Control**: Stage transitions and lifecycle management
- **📊 Timeline Tracking**: Progress tracking with timeline entries
- **🏃 Sprint Planning**: Sprint management and assignment
- **⚡ Performance Optimized**: Efficient API usage with proper pagination
- **🛡️ Error Handling**: Comprehensive error handling and reporting

## 📈 Performance Tips

1. **Use specific filters** to reduce API response sizes
2. **Implement pagination** for large result sets
3. **Cache frequently accessed data** locally
4. **Batch similar operations** when possible
5. **Use appropriate search namespaces** for better performance

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support with the DevRev MCP server:

- Check the troubleshooting section above
- Review the [DevRev API documentation](https://developer.devrev.ai)
- Contact DevRev support for API-related issues
