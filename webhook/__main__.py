"""
Docstring for webhook.__main__
"""

import uvicorn
from config.envconfig import EnvConfig


def main():
    """
    Docstring for main
    """
    config = EnvConfig()
    port = config.webhook_port
    host_address = config.host_address
    print("Hello from webhook!")
    uvicorn.run("webhook.main:app", host=host_address, port=port, reload=True)


if __name__ == "__main__":
    main()
