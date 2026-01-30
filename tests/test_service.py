"""Tests for mcp_service.service.

These tests use in-memory fakes for MongoDB and Kafka to avoid external dependencies.
"""

from __future__ import annotations
import pytest
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys
from mcp_service.service import (
    customer_init_indexes,
    customer_create,
    customer_get,
    customer_update,
    customer_delete,
    customer_list,
    player_publish_score_updated,
    player_publish_event,
    _db,
)


# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Fake MongoDB classes
# ---------------------------------------------------------------------------


class FakeInsertOneResult:
    def __init__(self, inserted_id: Any) -> None:
        self.inserted_id = inserted_id


class FakeUpdateResult:
    def __init__(self, matched_count: int, modified_count: int = 0) -> None:
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeDeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeCursor:
    def __init__(self, docs: List[Dict[str, Any]]) -> None:
        self.docs = docs

    def sort(self, key: str, direction: int) -> "FakeCursor":
        self.docs.sort(key=lambda x: x.get(key, ""), reverse=(direction == -1))
        return self

    def limit(self, n: int) -> "FakeCursor":
        self.docs = self.docs[:n]
        return self

    async def to_list(self, length: int) -> List[Dict[str, Any]]:
        return self.docs[:length]


class FakeCollection:
    def __init__(self) -> None:
        self.docs: List[Dict[str, Any]] = []

    async def create_index(self, key: str, unique: bool = False) -> None:
        # Mock index creation
        pass

    async def insert_one(self, doc: Dict[str, Any]) -> FakeInsertOneResult:
        if "_id" not in doc:
            doc["_id"] = len(self.docs) + 1
        self.docs.append(doc)
        return FakeInsertOneResult(doc["_id"])

    async def find_one(
        self, filter: Dict[str, Any], projection: Optional[Dict[str, int]] = None
    ) -> Optional[Dict[str, Any]]:
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in filter.items()):
                result = dict(doc)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                return result
        return None

    def find(
        self, filter: Dict[str, Any], projection: Optional[Dict[str, int]] = None
    ) -> FakeCursor:
        results = []
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in filter.items()):
                item = dict(doc)
                if projection and projection.get("_id") == 0:
                    item.pop("_id", None)
                results.append(item)
        # Sort by created_at descending
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return FakeCursor(results)

    async def update_one(
        self, filter: Dict[str, Any], update: Dict[str, Dict[str, Any]]
    ) -> FakeUpdateResult:
        matched = 0
        modified = 0
        if "$set" in update:
            for doc in self.docs:
                if all(doc.get(k) == v for k, v in filter.items()):
                    matched = 1
                    for field, value in update["$set"].items():
                        # Support dotted paths like "address.city"
                        parts = field.split(".")
                        target = doc
                        for part in parts[:-1]:
                            target = target.setdefault(part, {})
                        target[parts[-1]] = value
                    modified = 1
                    break
        return FakeUpdateResult(matched, modified)

    async def delete_one(self, filter: Dict[str, Any]) -> FakeDeleteResult:
        deleted = 0
        for idx, doc in enumerate(list(self.docs)):
            if all(doc.get(k) == v for k, v in filter.items()):
                self.docs.pop(idx)
                deleted = 1
                break
        return FakeDeleteResult(deleted)


class FakeDB:
    def __init__(self) -> None:
        self.customers = FakeCollection()


class FakeMongoClient:
    def __init__(self, uri: str) -> None:
        self.uri = uri
        self.db = FakeDB()

    def __getitem__(self, name: str) -> FakeDB:
        return self.db


# ---------------------------------------------------------------------------
# Fake Kafka classes
# ---------------------------------------------------------------------------


class FakeKafkaProducer:
    def __init__(self, bootstrap_servers: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.sent_messages: List[Dict[str, Any]] = []

    async def start(self) -> None:
        pass

    async def send_and_wait(self, topic: str, value: bytes, key: bytes) -> None:
        self.sent_messages.append(
            {
                "topic": topic,
                "value": json.loads(value.decode("utf-8")),
                "key": key.decode("utf-8"),
            }
        )

    async def stop(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def patched_mongo(monkeypatch) -> FakeMongoClient:
    """Patch the _mongo function to return our fake client."""
    fake_client = FakeMongoClient("mongodb://fake")

    def fake_mongo():
        return fake_client

    monkeypatch.setattr("mcp_service.service._mongo", fake_mongo)
    return fake_client


@pytest.fixture()
def patched_kafka(monkeypatch) -> FakeKafkaProducer:
    """Patch the _producer function to return our fake producer."""
    fake_producer = FakeKafkaProducer("localhost:9092")

    async def fake_producer_func():
        return fake_producer

    monkeypatch.setattr("mcp_service.service._producer", fake_producer_func)
    return fake_producer


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_customer_init_indexes(patched_mongo: FakeMongoClient) -> None:
    result = await customer_init_indexes.fn()
    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_customer_create_success(patched_mongo: FakeMongoClient) -> None:
    result = await customer_create.fn(
        customerid="123",
        firstname="John",
        lastname="Doe",
        email="john@example.com",
        phone="123-456-7890",
        street="123 Main St",
        city="Anytown",
        state="CA",
        zip="12345",
        country="USA",
    )
    assert result["customerid"] == "123"
    assert result["firstname"] == "John"
    assert result["lastname"] == "Doe"
    assert result["email"] == "john@example.com"
    assert result["phone"] == "123-456-7890"
    assert result["address"]["street"] == "123 Main St"
    assert "created_at" in result
    assert "updated_at" in result


@pytest.mark.asyncio
async def test_customer_create_incomplete_address() -> None:
    result = await customer_create.fn(
        customerid="123",
        firstname="John",
        lastname="Doe",
        email="john@example.com",
        street="123 Main St",
        # Missing city, state, zip, country
    )
    assert result == {
        "error": "address_incomplete",
        "message": "Provide street, city, state, zip, country",
    }


@pytest.mark.asyncio
async def test_customer_get_found(patched_mongo: FakeMongoClient) -> None:
    # First create a customer
    await customer_create.fn(
        customerid="123",
        firstname="John",
        lastname="Doe",
        email="john@example.com",
    )
    result = await customer_get.fn("123", "123")
    assert result["customerid"] == "123"
    assert result["firstname"] == "John"


@pytest.mark.asyncio
async def test_customer_get_not_found(patched_mongo: FakeMongoClient) -> None:
    result = await customer_get.fn("nonexistent", "nonexistent")
    assert result == {"error": "not_found", "customerid": "nonexistent"}


@pytest.mark.asyncio
async def test_customer_update_success(
    patched_mongo: FakeMongoClient, monkeypatch
) -> None:
    # Create customer
    await customer_create.fn(
        customerid="123",
        firstname="John",
        lastname="Doe",
        email="john@example.com",
    )

    # Mock customer_get since customer_update calls it
    async def mock_customer_get(customer_id):
        doc = await _db().customers.find_one({"customerid": customer_id}, {"_id": 0})
        return doc if doc else {"error": "not_found", "customerid": customer_id}

    monkeypatch.setattr("mcp_service.service.customer_get", mock_customer_get)
    # Update
    result = await customer_update.fn(
        customerid="123",
        firstname="Jane",
        email="jane@example.com",
    )
    assert result["customerid"] == "123"
    assert result["firstname"] == "Jane"
    assert result["email"] == "jane@example.com"


@pytest.mark.asyncio
async def test_customer_update_not_found(patched_mongo: FakeMongoClient) -> None:
    result = await customer_update.fn(customerid="nonexistent", firstname="Test")
    assert result == {"error": "not_found", "customerid": "nonexistent"}


@pytest.mark.asyncio
async def test_customer_delete_success(patched_mongo: FakeMongoClient) -> None:
    # Create customer
    await customer_create.fn(
        customerid="123",
        firstname="John",
        lastname="Doe",
        email="john@example.com",
    )
    result = await customer_delete.fn("123")
    assert result == {"deleted": True, "customerid": "123"}


@pytest.mark.asyncio
async def test_customer_delete_not_found(patched_mongo: FakeMongoClient) -> None:
    result = await customer_delete.fn("nonexistent")
    assert result == {"deleted": False, "customerid": "nonexistent"}


@pytest.mark.asyncio
async def test_customer_list(patched_mongo: FakeMongoClient) -> None:
    # Create some customers
    await customer_create.fn(
        customerid="1", firstname="A", lastname="B", email="a@b.com"
    )
    await customer_create.fn(
        customerid="2", firstname="C", lastname="D", email="c@d.com"
    )
    result = await customer_list.fn(limit=10)
    assert len(result) == 2
    assert result[0]["customerid"] in ["1", "2"]


@pytest.mark.asyncio
async def test_player_publish_score_updated(patched_kafka: FakeKafkaProducer) -> None:
    result = await player_publish_score_updated.fn(
        player_id="player1",
        delta=10,
        score_before=100,
        reason="match_win",
        match_id="match123",
    )
    assert result["published"] is True
    assert len(patched_kafka.sent_messages) == 1
    msg = patched_kafka.sent_messages[0]
    assert msg["topic"] == "player-events"  # Assuming default topic
    assert msg["value"]["event_type"] == "player.score.updated"
    assert msg["value"]["player_id"] == "player1"
    assert msg["value"]["data"]["delta"] == 10
    assert msg["value"]["data"]["score_after"] == 110


@pytest.mark.asyncio
async def test_player_publish_event(patched_kafka: FakeKafkaProducer) -> None:
    result = await player_publish_event.fn(
        event_type="player.level.up",
        player_id="player1",
        data={"level": 5, "xp": 1000},
    )
    assert result["published"] is True
    assert len(patched_kafka.sent_messages) == 1
    msg = patched_kafka.sent_messages[0]
    assert msg["value"]["event_type"] == "player.level.up"
    assert msg["value"]["player_id"] == "player1"
    assert msg["value"]["data"]["level"] == 5
