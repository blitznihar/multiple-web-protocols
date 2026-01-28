"""Tests for db.customer_db.CustomerDB.

These tests use a small in-memory fake MongoDB client so they do not
require a running Mongo instance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

import pytest

# Ensure project root (where db/ lives) is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.customer_db import CustomerDB  # noqa: E402


# ---------------------------------------------------------------------------
# In-memory fakes mimicking pymongo behaviour
# ---------------------------------------------------------------------------


class FakeInsertOneResult:
    def __init__(self, inserted_id: Any) -> None:
        self.inserted_id = inserted_id


class FakeUpdateResult:
    def __init__(self, modified_count: int) -> None:
        self.modified_count = modified_count


class FakeDeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self) -> None:
        self.docs: List[Dict[str, Any]] = []

    def insert_one(self, doc: Dict[str, Any]) -> FakeInsertOneResult:
        # Simulate MongoDB assigning an _id if not present
        if "_id" not in doc:
            doc["_id"] = len(self.docs) + 1
        self.docs.append(doc)
        return FakeInsertOneResult(doc["_id"])

    def find_one(
        self, filter: Dict[str, Any], projection: Optional[Dict[str, int]] = None
    ):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in filter.items()):
                result = dict(doc)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                return result
        return None

    def find(self, filter: Dict[str, Any], projection: Optional[Dict[str, int]] = None):
        results = []
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in filter.items()):
                item = dict(doc)
                if projection and projection.get("_id") == 0:
                    item.pop("_id", None)
                results.append(item)
        return results

    def update_one(
        self, filter: Dict[str, Any], update: Dict[str, Dict[str, Any]]
    ) -> FakeUpdateResult:
        modified = 0
        if "$set" in update:
            for doc in self.docs:
                if all(doc.get(k) == v for k, v in filter.items()):
                    for field, value in update["$set"].items():
                        # Support dotted paths like "address.city"
                        parts = field.split(".")
                        target = doc
                        for part in parts[:-1]:
                            target = target.setdefault(part, {})
                        target[parts[-1]] = value
                    modified = 1
                    break
        return FakeUpdateResult(modified)

    def delete_one(self, filter: Dict[str, Any]) -> FakeDeleteResult:
        deleted = 0
        for idx, doc in enumerate(list(self.docs)):
            if all(doc.get(k) == v for k, v in filter.items()):
                self.docs.pop(idx)
                deleted = 1
                break
        return FakeDeleteResult(deleted)


class FakeDB:
    def __init__(self) -> None:
        self.collections: Dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self.collections:
            self.collections[name] = FakeCollection()
        return self.collections[name]


class FakeMongoClient:
    def __init__(self, uri: str) -> None:  # uri kept for signature compatibility
        self.databases: Dict[str, FakeDB] = {}
        self.closed = False

    def __getitem__(self, name: str) -> FakeDB:
        if name not in self.databases:
            self.databases[name] = FakeDB()
        return self.databases[name]

    def close(self) -> None:
        self.closed = True


@pytest.fixture()
def patched_mongo(monkeypatch) -> FakeMongoClient:
    """Patch MongoClient in db.customer_db to use our in-memory fake."""

    from db import customer_db as customer_db_module

    fake_client = FakeMongoClient("mongodb://fake")

    def _fake_mongo_client(uri: str):  # type: ignore[override]
        # Ignore uri, always return same fake client for simplicity
        return fake_client

    monkeypatch.setattr(customer_db_module, "MongoClient", _fake_mongo_client)
    return fake_client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_create_customer_inserts_document_and_returns_id(
    patched_mongo: FakeMongoClient,
) -> None:
    uri = "mongodb://fake"
    db_name = "testdb"
    collection_name = "customers"
    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)

    customer = {
        "customerid": "C1",
        "firstname": "Alice",
        "lastname": "Smith",
    }

    inserted_id = db.create_customer(customer)

    assert inserted_id  # non-empty string
    collection: FakeCollection = db.collection  # type: ignore[assignment]
    assert len(collection.docs) == 1
    assert collection.docs[0]["customerid"] == "C1"


def test_get_customer_by_id_found(patched_mongo: FakeMongoClient) -> None:
    uri = "mongodb://fake"
    db_name = "testdb"
    collection_name = "customers"
    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)

    collection: FakeCollection = db.collection  # type: ignore[assignment]
    collection.insert_one({"customerid": "C1", "firstname": "Alice", "_id": 1})

    result = db.get_customer_by_id("C1")

    assert result is not None
    assert result["customerid"] == "C1"
    # _id should have been removed by projection
    assert "_id" not in result


def test_get_customer_by_id_not_found_returns_none(
    patched_mongo: FakeMongoClient,
) -> None:
    uri = "mongodb://fake"
    db_name = "testdb"
    collection_name = "customers"
    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)

    result = db.get_customer_by_id("missing")

    assert result is None


def test_list_customers_returns_all_documents(patched_mongo: FakeMongoClient) -> None:
    uri = "mongodb://fake"
    db_name = "testdb"
    collection_name = "customers"
    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)
    collection: FakeCollection = db.collection  # type: ignore[assignment]

    collection.insert_one({"customerid": "C1", "firstname": "Alice"})
    collection.insert_one({"customerid": "C2", "firstname": "Bob"})

    results = db.list_customers()

    assert {c["customerid"] for c in results} == {"C1", "C2"}
    for c in results:
        assert "_id" not in c


def test_update_customer_success_returns_true_and_updates_doc(
    patched_mongo: FakeMongoClient,
) -> None:
    uri = "mongodb://fake"
    db_name = "testdb"
    collection_name = "customers"
    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)
    collection: FakeCollection = db.collection  # type: ignore[assignment]

    collection.insert_one({"customerid": "C1", "lastname": "Old"})

    ok = db.update_customer("C1", {"lastname": "New", "address.city": "Testville"})

    assert ok is True
    doc = collection.find_one({"customerid": "C1"})
    assert doc["lastname"] == "New"
    assert doc["address"]["city"] == "Testville"


def test_update_customer_not_found_returns_false(
    patched_mongo: FakeMongoClient,
) -> None:
    uri = "mongodb://fake"
    db_name = "testdb"
    collection_name = "customers"
    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)

    ok = db.update_customer("missing", {"lastname": "New"})

    assert ok is False


def test_delete_customer_success_returns_true_and_removes_doc(
    patched_mongo: FakeMongoClient,
) -> None:
    uri = "mongodb://fake"
    db_name = "testdb"
    collection_name = "customers"
    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)
    collection: FakeCollection = db.collection  # type: ignore[assignment]

    collection.insert_one({"customerid": "C1"})

    ok = db.delete_customer("C1")

    assert ok is True
    assert collection.find_one({"customerid": "C1"}) is None


def test_delete_customer_not_found_returns_false(
    patched_mongo: FakeMongoClient,
) -> None:
    uri = "mongodb://fake"
    db_name = "testdb"
    collection_name = "customers"
    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)

    ok = db.delete_customer("missing")

    assert ok is False


def test_close_calls_underlying_client_close(patched_mongo: FakeMongoClient) -> None:
    uri = "mongodb://fake"
    db_name = "testdb"
    collection_name = "customers"
    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)

    db.close()

    assert patched_mongo.closed is True
