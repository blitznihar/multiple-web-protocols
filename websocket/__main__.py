"""
Docstring for websocket.__main__
"""

import uvicorn
from config.envconfig import EnvConfig


def main():
    """
    Docstring for main
    """
    print("Hello from web socket!")
    config = EnvConfig()
    port = config.websocket_port
    host = config.host
    print(f"Starting WebSocket server on {host}:{port}...")

    uvicorn.run("websocket.service:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
