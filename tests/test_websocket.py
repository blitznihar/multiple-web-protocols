"""Tests for the websocket service."""

from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import websocket.service as ws_service  # noqa: E402


class FakeWebSocketManager:
    """In-memory stand-in for WebSocketManager."""

    def __init__(self) -> None:
        self.connections = []

    async def connect(self, ws) -> None:
        self.connections.append(ws)

    async def disconnect(self, ws) -> None:
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, message: str) -> None:
        pass  # Mock broadcast


class FakeKafkaConsumer:
    """Mock Kafka consumer."""

    def __init__(self, manager):  # noqa: ARG002
        pass

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass


@pytest.fixture()
def fake_manager(monkeypatch) -> FakeWebSocketManager:
    """Provide a fake manager and patch websocket.service.manager."""
    manager = FakeWebSocketManager()
    monkeypatch.setattr(ws_service, "manager", manager)
    return manager


@pytest.fixture()
def fake_consumer(monkeypatch, fake_manager: FakeWebSocketManager) -> FakeKafkaConsumer:
    """Provide a fake consumer and patch websocket.service.consumer."""
    consumer = FakeKafkaConsumer(fake_manager)
    monkeypatch.setattr(ws_service, "consumer", consumer)
    return consumer


@pytest.fixture()
def client(
    fake_manager: FakeWebSocketManager, fake_consumer: FakeKafkaConsumer
) -> TestClient:  # noqa: ARG001
    """FastAPI test client for websocket service."""
    return TestClient(ws_service.app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# WebSocket /ws
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_websocket_connection(fake_manager: FakeWebSocketManager) -> None:
    """Test WebSocket connection using a mock WebSocket."""
    # This is a basic test; for full WebSocket testing, you'd need a test server
    # and a WebSocket client library like 'websockets'

    # Mock WebSocket object
    mock_ws = MagicMock()
    mock_ws.receive_text = AsyncMock(side_effect=["hello", KeyboardInterrupt])

    # Test connect
    await fake_manager.connect(mock_ws)
    assert mock_ws in fake_manager.connections

    # Test disconnect
    await fake_manager.disconnect(mock_ws)
    assert mock_ws not in fake_manager.connections


# Note: For comprehensive WebSocket testing, you would need to:
# 1. Add pytest-asyncio to dev dependencies
# 2. Add websockets library
# 3. Use a test server and actual WebSocket connections
# Example:
#
# import websockets
# from fastapi.testclient import TestClient
# from fastapi import FastAPI
#
# @pytest.mark.asyncio
# async def test_websocket_real():
#     # Start test server
#     # Connect with websockets client
#     # Send/receive messages
#     pass
