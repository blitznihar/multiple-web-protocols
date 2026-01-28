"""Tests for the FastAPI app in rest.app."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so `rest` and `db` packages import.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import rest.app as rest_app  # noqa: E402


class FakeCustomerDB:
    """In-memory stand-in for CustomerDB used by the REST API tests."""

    def __init__(self) -> None:
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.healthy: bool = True

    # Health check used by /health
    def health_check(self) -> bool:
        return self.healthy

    # CRUD operations used by the endpoints
    def list_customers(self) -> List[Dict[str, Any]]:
        return list(self.customers.values())

    def get_customer_by_id(self, customerid: str) -> Optional[Dict[str, Any]]:
        return self.customers.get(customerid)

    def create_customer(self, customer: Dict[str, Any]) -> str:
        cid = customer["customerid"]
        self.customers[cid] = dict(customer)
        return cid

    def update_customer(self, customerid: str, updates: Dict[str, Any]) -> bool:
        if customerid not in self.customers:
            return False
        existing = self.customers[customerid]
        # Simple deep-merge for nested address dicts
        for key, value in updates.items():
            if key == "address" and isinstance(value, dict):
                existing.setdefault("address", {})
                existing["address"].update(value)
            else:
                existing[key] = value
        return True

    def delete_customer(self, customerid: str) -> bool:
        if customerid in self.customers:
            del self.customers[customerid]
            return True
        return False


@pytest.fixture()
def fake_db(monkeypatch) -> FakeCustomerDB:
    """Provide a fake DB and patch rest.app.db to use it."""

    db = FakeCustomerDB()
    monkeypatch.setattr(rest_app, "db", db)
    return db


@pytest.fixture()
def client(fake_db: FakeCustomerDB) -> TestClient:  # noqa: ARG001
    """FastAPI test client bound to the patched app."""

    return TestClient(rest_app.app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health_ok(client: TestClient, fake_db: FakeCustomerDB) -> None:
    fake_db.healthy = True

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mongo": "ok"}


def test_health_unhealthy(client: TestClient, fake_db: FakeCustomerDB) -> None:
    fake_db.healthy = False

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == "MongoDB not healthy"


# ---------------------------------------------------------------------------
# /customers (list & get)
# ---------------------------------------------------------------------------


def test_list_customers_returns_all(
    client: TestClient, fake_db: FakeCustomerDB
) -> None:
    fake_db.customers = {
        "C1": {
            "customerid": "C1",
            "firstname": "Alice",
            "lastname": "Smith",
            "email": "alice@example.com",
            "phone": "+1-555-0000",
        },
        "C2": {
            "customerid": "C2",
            "firstname": "Bob",
            "lastname": "Jones",
            "email": "bob@example.com",
            "phone": "+1-555-0001",
        },
    }

    response = client.get("/customers")

    assert response.status_code == 200
    body = response.json()
    assert {c["customerid"] for c in body} == {"C1", "C2"}


def test_get_customer_found(client: TestClient, fake_db: FakeCustomerDB) -> None:
    fake_db.customers["C1"] = {
        "customerid": "C1",
        "firstname": "Alice",
        "lastname": "Smith",
        "email": "alice@example.com",
        "phone": "+1-555-0000",
    }

    response = client.get("/customers/C1")

    assert response.status_code == 200
    assert response.json()["customerid"] == "C1"


def test_get_customer_not_found(client: TestClient, fake_db: FakeCustomerDB) -> None:  # noqa: ARG001
    response = client.get("/customers/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


# ---------------------------------------------------------------------------
# POST /customers
# ---------------------------------------------------------------------------


def test_create_customer_success(client: TestClient, fake_db: FakeCustomerDB) -> None:
    payload = {
        "customerid": "C1",
        "firstname": "Alice",
        "lastname": "Smith",
        "email": "alice@example.com",
        "phone": "+1-555-0000",
    }

    response = client.post("/customers", json=payload)

    assert response.status_code == 201
    assert response.json() == {"message": "created", "customerid": "C1"}
    assert "C1" in fake_db.customers


def test_create_customer_conflict_when_id_exists(
    client: TestClient, fake_db: FakeCustomerDB
) -> None:
    fake_db.customers["C1"] = {
        "customerid": "C1",
        "firstname": "Existing",
        "lastname": "User",
        "email": "existing@example.com",
        "phone": "+1-555-1111",
    }

    payload = {
        "customerid": "C1",
        "firstname": "Alice",
        "lastname": "Smith",
        "email": "alice@example.com",
        "phone": "+1-555-0000",
    }

    response = client.post("/customers", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "customerid already exists"


# ---------------------------------------------------------------------------
# PUT /customers/{customerid}
# ---------------------------------------------------------------------------


def test_update_customer_no_fields_returns_400(
    client: TestClient, fake_db: FakeCustomerDB
) -> None:  # noqa: ARG001
    response = client.put("/customers/C1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields provided to update"


def test_update_customer_not_found_returns_404(
    client: TestClient, fake_db: FakeCustomerDB
) -> None:  # noqa: ARG001
    response = client.put("/customers/C1", json={"firstname": "New"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found (or no changes)"


def test_update_customer_success(client: TestClient, fake_db: FakeCustomerDB) -> None:
    fake_db.customers["C1"] = {
        "customerid": "C1",
        "firstname": "Old",
        "lastname": "Name",
        "email": "alice@example.com",
        "phone": "+1-555-0000",
        "address": {
            "street": "123 Main St",
            "city": "Old City",
            "state": "TS",
            "zip": "12345",
            "country": "Testland",
        },
    }

    response = client.put(
        "/customers/C1",
        json={
            "firstname": "New",
            "address": {
                "street": "123 Main St",
                "city": "New City",
                "state": "TS",
                "zip": "12345",
                "country": "Testland",
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "updated", "customerid": "C1"}
    updated = fake_db.customers["C1"]
    assert updated["firstname"] == "New"
    assert updated["address"]["city"] == "New City"


# ---------------------------------------------------------------------------
# DELETE /customers/{customerid}
# ---------------------------------------------------------------------------


def test_delete_customer_not_found_returns_404(
    client: TestClient, fake_db: FakeCustomerDB
) -> None:  # noqa: ARG001
    response = client.delete("/customers/C1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_delete_customer_success(client: TestClient, fake_db: FakeCustomerDB) -> None:
    fake_db.customers["C1"] = {
        "customerid": "C1",
        "firstname": "Alice",
        "lastname": "Smith",
        "email": "alice@example.com",
        "phone": "+1-555-0000",
    }

    response = client.delete("/customers/C1")

    assert response.status_code == 200
    assert response.json() == {"message": "deleted", "customerid": "C1"}
    assert "C1" not in fake_db.customers
