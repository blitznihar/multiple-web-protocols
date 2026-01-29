"""Tests for the webhook service."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import sys
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import webhook.main as webhook_main  # noqa: E402


class FakeSubscriptionRegistry:
    """In-memory stand-in for SubscriptionRegistry."""

    def __init__(self) -> None:
        self.subscriptions: Dict[str, Dict[str, Any]] = {}

    async def list(self) -> List[MagicMock]:
        mocks = []
        for sub_data in self.subscriptions.values():
            mock_sub = MagicMock()
            mock_sub.model_dump.return_value = sub_data
            mocks.append(mock_sub)
        return mocks

    async def add(
        self,
        *,
        url: str,
        event_types: List[str],
        secret: str,
        player_id: Optional[str] = None,
    ) -> MagicMock:
        import uuid
        from datetime import datetime, timezone

        sub_id = str(uuid.uuid4())
        sub_data = {
            "subscription_id": sub_id,
            "url": url,
            "event_types": event_types,
            "secret": secret,
            "player_id": player_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.subscriptions[sub_id] = sub_data

        # Return a mock that has model_dump method
        mock_sub = MagicMock()
        mock_sub.model_dump.return_value = sub_data
        return mock_sub

    async def disable(self, subscription_id: str) -> bool:
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]["is_active"] = False
            return True
        return False


class FakeKafkaConsumer:
    """Mock Kafka consumer."""

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass


@pytest.fixture()
def fake_registry(monkeypatch) -> FakeSubscriptionRegistry:
    """Provide a fake registry and patch webhook.main.registry."""
    registry = FakeSubscriptionRegistry()
    monkeypatch.setattr(webhook_main, "registry", registry)
    return registry


@pytest.fixture()
def fake_consumer(monkeypatch) -> FakeKafkaConsumer:
    """Provide a fake consumer and patch webhook.main.consumer."""
    consumer = FakeKafkaConsumer()
    monkeypatch.setattr(webhook_main, "consumer", consumer)
    return consumer


@pytest.fixture()
def client(
    fake_registry: FakeSubscriptionRegistry, fake_consumer: FakeKafkaConsumer
) -> TestClient:  # noqa: ARG001
    """FastAPI test client for webhook service."""
    return TestClient(webhook_main.app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /webhooks
# ---------------------------------------------------------------------------


def test_list_webhooks_empty(
    client: TestClient, fake_registry: FakeSubscriptionRegistry
) -> None:  # noqa: ARG001
    response = client.get("/webhooks")
    assert response.status_code == 200
    assert response.json() == []


def test_create_webhook(
    client: TestClient, fake_registry: FakeSubscriptionRegistry
) -> None:
    payload = {
        "url": "https://example.com/hook",
        "event_types": ["player.score.updated"],
        "secret": "mysecret",
        "player_id": "player123",
    }
    response = client.post("/webhooks", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == payload["url"]
    assert data["event_types"] == payload["event_types"]
    assert data["secret"] == payload["secret"]
    assert data["player_id"] == payload["player_id"]
    assert data["is_active"] is True
    assert "subscription_id" in data
    assert "created_at" in data


def test_create_webhook_minimal(
    client: TestClient, fake_registry: FakeSubscriptionRegistry
) -> None:
    payload = {
        "url": "https://example.com/hook",
        "event_types": ["player.score.updated"],
        "secret": "mysecret",
    }
    response = client.post("/webhooks", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] is None


def test_list_webhooks_after_create(
    client: TestClient, fake_registry: FakeSubscriptionRegistry
) -> None:
    # Create one
    payload = {
        "url": "https://example.com/hook",
        "event_types": ["player.score.updated"],
        "secret": "mysecret",
    }
    client.post("/webhooks", json=payload)

    response = client.get("/webhooks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["url"] == payload["url"]


def test_disable_webhook(
    client: TestClient, fake_registry: FakeSubscriptionRegistry
) -> None:
    # Create one
    payload = {
        "url": "https://example.com/hook",
        "event_types": ["player.score.updated"],
        "secret": "mysecret",
    }
    create_resp = client.post("/webhooks", json=payload)
    sub_id = create_resp.json()["subscription_id"]

    # Disable it
    response = client.delete(f"/webhooks/{sub_id}")
    assert response.status_code == 200
    assert response.json() == {"disabled": True, "subscription_id": sub_id}

    # Check it's disabled
    list_resp = client.get("/webhooks")
    subs = list_resp.json()
    assert len(subs) == 1
    assert subs[0]["is_active"] is False


def test_disable_webhook_not_found(
    client: TestClient, fake_registry: FakeSubscriptionRegistry
) -> None:  # noqa: ARG001
    response = client.delete("/webhooks/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "subscription not found"
