# DevRev MCP Server

## Overview

A Model Context Protocol server for DevRev. This server provides comprehensive access to DevRev's APIs, allowing you to manage work items (issues, tickets), parts (enhancements), search across your DevRev data, and retrieve user information.

## Tools

### Search & Discovery
- **`search`**: Search for information across DevRev using the search API with support for different namespaces (articles, issues, tickets, parts, dev_users, accounts, rev_orgs).
- **`get_current_user`**: Fetch details about the currently authenticated DevRev user.

### Work Items (Issues & Tickets)
- **`get_work`**: Get comprehensive information about a specific DevRev work item using its ID.
- **`create_work`**: Create new issues or tickets in DevRev with specified properties like title, body, assignees, and associated parts.
- **`update_work`**: Update existing work items by modifying properties such as title, body, assignees, or associated parts.
- **`list_works`**: List and filter work items based on various criteria like state, dates, assignees, parts, and more.

### Parts (Enhancements)
- **`get_part`**: Get detailed information about a specific part (enhancement) using its ID.
- **`create_part`**: Create new parts (enhancements) with specified properties including name, description, assignees, and parent parts.
- **`update_part`**: Update existing parts by modifying properties such as name, description, assignees, or target dates.
- **`list_parts`**: List and filter parts based on various criteria like dates, assignees, parent parts, and more.

## Configuration

### Get the DevRev API Key

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

- **Comprehensive Work Item Management**: Create, read, update, and list both issues and tickets
- **Enhanced Part Management**: Full CRUD operations for parts (enhancements) including hierarchical relationships
- **Advanced Search**: Search across multiple namespaces with hybrid search capabilities
- **Flexible Filtering**: Advanced filtering options for listing work items and parts based on dates, assignees, states, and more
- **User Context**: Access to current user information for personalized experiences
- **Rich Data Support**: Handle complex relationships between work items, parts, users, and organizations
