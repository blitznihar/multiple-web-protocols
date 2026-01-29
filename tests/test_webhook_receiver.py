"""Tests for the webhook receiver service."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import webhook_receiver.service as webhook_receiver_service  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    """FastAPI test client for webhook receiver service."""
    return TestClient(webhook_receiver_service.app)


def test_hook_endpoint(client: TestClient) -> None:
    payload = {"event": "player.score.updated", "player_id": "123", "score": 100}
    headers = {
        "X-Webhook-Signature": "signature123",
        "Content-Type": "application/json",
    }

    response = client.post("/hook", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_hook_endpoint_empty_body(client: TestClient) -> None:
    response = client.post("/hook", json={})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_hook_endpoint_with_headers(client: TestClient) -> None:
    payload = {"data": "test"}
    headers = {"Authorization": "Bearer token", "User-Agent": "TestAgent"}

    response = client.post("/hook", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"ok": True}
