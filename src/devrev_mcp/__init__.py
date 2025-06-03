"""
Copyright (c) 2025 DevRev, Inc.
SPDX-License-Identifier: MIT

DevRev MCP Server package.
This package provides a FastMCP-based server for interacting with DevRev APIs.
"""

from .server import main, mcp

__version__ = "0.1.1"
__all__ = ["main", "mcp"]

# Export the main function for the CLI entry point
def main_cli():
    """CLI entry point for the DevRev MCP server."""
    main()
