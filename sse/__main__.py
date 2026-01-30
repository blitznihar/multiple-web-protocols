"""
Docstring for sse.__main__
"""

from config.envconfig import EnvConfig
from mcp_service.service import mcp


def main():
    """
    Docstring for main
    """
    config = EnvConfig()
    port = config.sse_port
    host = config.host
    print(f"Starting SSE server on {host}:{port}...")
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
