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

## Prerequisites

Before using this MCP server, you need to install either `uvx` or `uv`, which are modern Python package and project management tools.

### Installing uv (Recommended)

`uv` is a fast Python package installer and resolver. It includes `uvx` for running Python applications.

#### On macOS and Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### On Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Alternative Installation Methods:

**Using Homebrew (macOS):**
```bash
brew install uv
```

**Using pip:**
```bash
pip install uv
```

### Verifying Installation

After installation, verify that `uv` and `uvx` are available:

```bash
# Check uv version
uv --version

# Check uvx version  
uvx --version
```

Both commands should return version information. If you get "command not found" errors, you may need to restart your terminal or add the installation directory to your PATH.

### Troubleshooting

If you encounter issues:
1. Restart your terminal after installation
2. Check that the installation directory is in your PATH
3. On macOS/Linux, the default installation adds uv to `~/.cargo/bin/`
4. Refer to the [official uv documentation](https://docs.astral.sh/uv/) for more detailed installation instructions

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
