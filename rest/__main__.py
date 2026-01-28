"""
Docstring for rest.__main__
"""

import uvicorn
from config.envconfig import EnvConfig


def main():
    """
    Docstring for main
    """
    config = EnvConfig()
    port = config.restapi_port
    host = config.host
    print(f"Starting REST API server on {host}:{port}...")

    uvicorn.run("rest.app:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
