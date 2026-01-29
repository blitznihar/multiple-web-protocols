"""
Docstring for webhook.__main__
"""

import uvicorn
from config.envconfig import EnvConfig


def main():
    config = EnvConfig()
    uvicorn.run(
        "webhook_receiver.service:app",
        host=config.host_address,
        port=config.webhook_receiver_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
