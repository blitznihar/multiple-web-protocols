"""Tests for config/envconfig.py EnvConfig class."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.envconfig import EnvConfig  # noqa: E402


@pytest.fixture()
def env_config() -> EnvConfig:
    """Provide a fresh EnvConfig instance for each test."""
    return EnvConfig()


# ---------------------------------------------------------------------------
# String properties with defaults
# ---------------------------------------------------------------------------


def test_database_url_default(env_config: EnvConfig) -> None:
    """Test database_url returns default when env var not set."""
    assert env_config.database_url == "mongodb://localhost:27017"


def test_database_url_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test database_url reads from MONGODB_URI env var."""
    monkeypatch.setenv("MONGODB_URI", "mongodb://custom:27017")
    assert env_config.database_url == "mongodb://custom:27017"


def test_secret_key_default(env_config: EnvConfig) -> None:
    """Test secret_key returns default."""
    assert env_config.secret_key == "default_secret_key"


def test_secret_key_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test secret_key reads from SECRET_KEY env var."""
    monkeypatch.setenv("SECRET_KEY", "my_secret")
    assert env_config.secret_key == "my_secret"


def test_api_key_default(env_config: EnvConfig) -> None:
    """Test api_key returns empty string by default."""
    assert env_config.api_key == ""


def test_api_key_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test api_key reads from API_KEY env var."""
    monkeypatch.setenv("API_KEY", "abc123")
    assert env_config.api_key == "abc123"


def test_log_level_default(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test log_level returns 'INFO' by default."""
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert env_config.log_level == "INFO"


def test_log_level_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test log_level reads from LOG_LEVEL env var."""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    assert env_config.log_level == "DEBUG"


def test_db_name_default(env_config: EnvConfig) -> None:
    """Test db_name returns 'customerdb' by default."""
    assert env_config.db_name == "customerdb"


def test_db_name_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test db_name reads from MONGO_DB env var."""
    monkeypatch.setenv("MONGO_DB", "testdb")
    assert env_config.db_name == "testdb"


def test_collection_name_default(env_config: EnvConfig) -> None:
    """Test collection_name returns 'customers' by default."""
    assert env_config.collection_name == "customers"


def test_collection_name_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test collection_name reads from MONGO_COLLECTION env var."""
    monkeypatch.setenv("MONGO_COLLECTION", "users")
    assert env_config.collection_name == "users"


def test_host_default(env_config: EnvConfig) -> None:
    """Test host returns 'localhost' by default."""
    assert env_config.host == "localhost"


def test_host_from_env(monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig) -> None:
    """Test host reads from HOST env var."""
    monkeypatch.setenv("HOST", "0.0.0.0")
    assert env_config.host == "0.0.0.0"


def test_cors_origins_default(env_config: EnvConfig) -> None:
    """Test cors_origins returns '*' by default."""
    assert env_config.cors_origins == "*"


def test_cors_origins_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test cors_origins reads from CORS_ORIGINS env var."""
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    assert env_config.cors_origins == "http://localhost:3000"


def test_host_address_default(env_config: EnvConfig) -> None:
    """Test host_address returns '0.0.0.0' by default."""
    assert env_config.host_address == "0.0.0.0"


def test_host_address_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test host_address reads from HOST_ADDRESS env var."""
    monkeypatch.setenv("HOST_ADDRESS", "127.0.0.1")
    assert env_config.host_address == "127.0.0.1"


# ---------------------------------------------------------------------------
# Boolean property
# ---------------------------------------------------------------------------


def test_debug_mode_default(env_config: EnvConfig) -> None:
    """Test debug_mode returns False by default."""
    assert env_config.debug_mode is False


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("t", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("f", False),
        ("anything_else", False),
    ],
)
def test_debug_mode_from_env(
    monkeypatch: pytest.MonkeyPatch,
    env_config: EnvConfig,
    env_value: str,
    expected: bool,
) -> None:
    """Test debug_mode parses various string values to bool."""
    monkeypatch.setenv("DEBUG_MODE", env_value)
    assert env_config.debug_mode is expected


# ---------------------------------------------------------------------------
# Integer properties (ports)
# ---------------------------------------------------------------------------


def test_graphql_port_default(env_config: EnvConfig) -> None:
    """Test graphql_port returns 8061 by default."""
    assert env_config.graphql_port == 8061


def test_graphql_port_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test graphql_port reads and parses GRAPHQL_PORT env var."""
    monkeypatch.setenv("GRAPHQL_PORT", "9000")
    assert env_config.graphql_port == 9000


def test_websocket_port_default(env_config: EnvConfig) -> None:
    """Test websocket_port returns 8068 by default."""
    assert env_config.websocket_port == 8068


def test_websocket_port_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test websocket_port reads and parses WEBSOCKET_PORT env var."""
    monkeypatch.setenv("WEBSOCKET_PORT", "9001")
    assert env_config.websocket_port == 9001


def test_restapi_port_default(env_config: EnvConfig) -> None:
    """Test restapi_port returns 8060 by default."""
    assert env_config.restapi_port == 8060


def test_restapi_port_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test restapi_port reads and parses REST_PORT env var."""
    monkeypatch.setenv("REST_PORT", "8080")
    assert env_config.restapi_port == 8080


def test_grpc_port_default(env_config: EnvConfig) -> None:
    """Test grpc_port returns 8062 by default."""
    assert env_config.grpc_port == 8062


def test_grpc_port_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test grpc_port reads and parses GRPC_PORT env var."""
    monkeypatch.setenv("GRPC_PORT", "50052")
    assert env_config.grpc_port == 50052


def test_soap_port_default(env_config: EnvConfig) -> None:
    """Test soap_port returns 8067 by default."""
    assert env_config.soap_port == 8067


def test_soap_port_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test soap_port reads and parses SOAP_PORT env var."""
    monkeypatch.setenv("SOAP_PORT", "8070")
    assert env_config.soap_port == 8070


def test_mcp_port_default(env_config: EnvConfig) -> None:
    """Test mcp_port returns 8064 by default."""
    assert env_config.mcp_port == 8064


def test_mcp_port_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test mcp_port reads and parses MCP_PORT env var."""
    monkeypatch.setenv("MCP_PORT", "8065")
    assert env_config.mcp_port == 8065


def test_amqp_port_default(env_config: EnvConfig) -> None:
    """Test amqp_port returns 8070 by default."""
    assert env_config.amqp_port == 8070


def test_amqp_port_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test amqp_port reads and parses AMQP_PORT env var."""
    monkeypatch.setenv("AMQP_PORT", "5672")
    assert env_config.amqp_port == 5672


def test_mqtt_port_default(env_config: EnvConfig) -> None:
    """Test mqtt_port returns 8071 by default."""
    assert env_config.mqtt_port == 8071


def test_mqtt_port_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test mqtt_port reads and parses MQTT_PORT env var."""
    monkeypatch.setenv("MQTT_PORT", "1883")
    assert env_config.mqtt_port == 1883


def test_webhook_port_default(env_config: EnvConfig) -> None:
    """Test webhook_port returns 8069 by default."""
    assert env_config.webhook_port == 8069


def test_webhook_port_from_env(
    monkeypatch: pytest.MonkeyPatch, env_config: EnvConfig
) -> None:
    """Test webhook_port reads and parses WEBHOOK_PORT env var."""
    monkeypatch.setenv("WEBHOOK_PORT", "8072")
    assert env_config.webhook_port == 8072
