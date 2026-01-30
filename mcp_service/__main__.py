"""
Main entry point for MCP server
"""

from .service import mcp
from config.envconfig import EnvConfig


def main():
    """
    Docstring for main
    """
    config = EnvConfig()
    port = config.mcp_port
    host = config.host
    print(f"Starting MCP server on {host}:{port}...")
    mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()
