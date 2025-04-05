# DevRev MCP server

## Overview

A Model Context Protocol server for DevRev. It is used to search and retrieve information using the DevRev APIs.

## Tools

- `search`: Search for information using the DevRev search API with the provided query and namespace.
- `get_object`: Get all information about a DevRev issue or ticket using its ID.

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
