import os
from dotenv import load_dotenv

load_dotenv()


class EnvConfig:
    """Class to manage environment configurations."""

    @property
    def database_url(self) -> str:
        """Get the database URL from environment variables."""
        return os.getenv("MONGODB_URI", "mongodb://localhost:27017")

    @property
    def secret_key(self) -> str:
        """Get the secret key from environment variables."""
        return os.getenv("SECRET_KEY", "default_secret_key")

    @property
    def debug_mode(self) -> bool:
        """Get the debug mode status from environment variables."""
        return os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t")

    @property
    def api_key(self) -> str:
        """Get the API key from environment variables."""
        return os.getenv("API_KEY", "")

    @property
    def log_level(self) -> str:
        """Get the log level from environment variables."""
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def db_name(self) -> str:
        """Get the database name from environment variables."""
        return os.getenv("MONGO_DB", "customerdb")

    @property
    def collection_name(self) -> str:
        """Get the collection name from environment variables."""
        return os.getenv("MONGO_COLLECTION", "customers")

    @property
    def graphql_port(self) -> int:
        """Get the GraphQL port from environment variables."""
        return int(os.getenv("GRAPHQL_PORT", "8061"))

    @property
    def websocket_port(self) -> int:
        """Get the WebSocket port from environment variables."""
        return int(os.getenv("WEBSOCKET_PORT", "8068"))

    @property
    def restapi_port(self) -> int:
        """Get the REST API port from environment variables."""
        return int(os.getenv("REST_PORT", "8060"))

    @property
    def grpc_port(self) -> int:
        """Get the gRPC port from environment variables."""
        return int(os.getenv("GRPC_PORT", "8062"))

    @property
    def soap_port(self) -> int:
        """Get the SOAP port from environment variables."""
        return int(os.getenv("SOAP_PORT", "8067"))

    @property
    def mcp_port(self) -> int:
        """Get the MCP port from environment variables."""
        return int(os.getenv("MCP_PORT", "8064"))

    @property
    def amqp_port(self) -> int:
        """Get the AMQP port from environment variables."""
        return int(os.getenv("AMQP_PORT", "8070"))

    @property
    def mqtt_port(self) -> int:
        """Get the MQTT port from environment variables."""
        return int(os.getenv("MQTT_PORT", "8071"))

    @property
    def webhook_port(self) -> int:
        """Get the Webhook port from environment variables."""
        return int(os.getenv("WEBHOOK_PORT", "8069"))

    @property
    def host(self) -> str:
        """Get the host from environment variables."""
        return os.getenv("HOST", "localhost")

    @property
    def cors_origins(self) -> str:
        """Get the CORS origins from environment variables."""
        return os.getenv("CORS_ORIGINS", "*")

    @property
    def host_address(self) -> str:
        """Get the host address from environment variables."""
        return os.getenv("HOST_ADDRESS", "0.0.0.0")
