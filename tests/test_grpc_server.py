"""Tests for grpc_service.server.CustomerService and helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path
import sys

import grpc

# Ensure project root (where grpc_service lives) is on sys.path when running tests.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from grpc_service.customerpb import customer_pb2
from grpc_service import server as grpc_server


class DummyContext:
    """Minimal context used to capture status and details in tests."""

    def __init__(self) -> None:
        self.code: Optional[grpc.StatusCode] = None
        self.details: Optional[str] = None

    def set_code(self, code: grpc.StatusCode) -> None:
        self.code = code

    def set_details(self, details: str) -> None:
        self.details = details


class FakeCustomerDB:
    """In‑memory stand‑in for CustomerDB used in unit tests."""

    def __init__(self) -> None:
        self.created: list[Dict[str, Any]] = []
        self.by_id: Dict[str, Dict[str, Any]] = {}
        self.update_result: Dict[str, bool] = {}
        self.delete_result: Dict[str, bool] = {}
        self.raise_on_create: Optional[BaseException] = None

    def create_customer(self, customer: Dict[str, Any]) -> str:
        if self.raise_on_create is not None:
            raise self.raise_on_create
        self.created.append(customer)
        cid = customer["customerid"]
        self.by_id[cid] = customer
        return cid

    def get_customer_by_id(self, customerid: str) -> Optional[Dict[str, Any]]:
        return self.by_id.get(customerid)

    def list_customers(self):  # pragma: no cover - not used yet
        return list(self.by_id.values())

    def update_customer(self, customerid: str, updates: Dict[str, Any]) -> bool:
        result = self.update_result.get(customerid, False)
        if result and customerid in self.by_id:
            self.by_id[customerid].update(updates)
        return result

    def delete_customer(self, customerid: str) -> bool:
        return self.delete_result.get(customerid, False)


def make_customer_msg(**overrides: Any) -> customer_pb2.Customer:
    """Helper to build a Customer protobuf message for tests."""

    base_addr = {
        "street": "123 Main St",
        "city": "Testville",
        "state": "TS",
        "zip": "12345",
        "country": "Testland",
    }
    addr = {**base_addr, **overrides.pop("address", {})}

    return customer_pb2.Customer(
        customerid=overrides.get("customerid", "C1"),
        firstname=overrides.get("firstname", "Alice"),
        lastname=overrides.get("lastname", "Smith"),
        email=overrides.get("email", "alice@example.com"),
        phone=overrides.get("phone", "+1-555-0000"),
        address=customer_pb2.Address(**addr),
    )


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


def test_customer_msg_to_dict_with_address():
    msg = make_customer_msg(customerid="123")

    result = grpc_server.customer_msg_to_dict(msg)

    assert result["customerid"] == "123"
    assert result["firstname"] == "Alice"
    assert result["address"]["city"] == "Testville"


def test_customer_msg_to_dict_without_address():
    # Address fields all blank should be omitted from the document
    empty_addr = customer_pb2.Address(
        street="",
        city="",
        state="",
        zip="",
        country="",
    )
    msg = customer_pb2.Customer(
        customerid="123",
        firstname="Alice",
        lastname="Smith",
        email="alice@example.com",
        phone="+1-555-0000",
        address=empty_addr,
    )

    result = grpc_server.customer_msg_to_dict(msg)

    assert "address" not in result


def test_dict_to_customer_msg_roundtrip():
    original = {
        "customerid": "123",
        "firstname": "Alice",
        "lastname": "Smith",
        "email": "alice@example.com",
        "phone": "+1-555-0000",
        "address": {
            "street": "123 Main St",
            "city": "Testville",
            "state": "TS",
            "zip": "12345",
            "country": "Testland",
        },
    }

    msg = grpc_server.dict_to_customer_msg(original)

    assert msg.customerid == original["customerid"]
    assert msg.address.city == original["address"]["city"]


def test_build_update_dict_includes_only_non_empty_fields():
    msg = make_customer_msg(
        firstname="",  # should be ignored
        lastname="NewLast",
        address={
            "street": "",  # ignored
            "city": "New City",
        },
    )

    updates = grpc_server.build_update_dict(msg)

    assert "firstname" not in updates
    assert updates["lastname"] == "NewLast"
    # Address fields are flattened with "address." prefix
    assert updates["address.city"] == "New City"
    assert "address.street" not in updates


# ---------------------------------------------------------------------------
# CustomerService tests (with FakeCustomerDB)
# ---------------------------------------------------------------------------


def make_service_with_fake_db(fake_db: FakeCustomerDB) -> grpc_server.CustomerService:
    # Bypass __init__ to avoid opening a real Mongo connection.
    service = grpc_server.CustomerService.__new__(
        grpc_server.CustomerService
    )  # type: ignore[misc]
    service.db = fake_db  # type: ignore[assignment]
    return service


def test_create_customer_missing_id_sets_invalid_argument():
    fake_db = FakeCustomerDB()
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    req = customer_pb2.CreateCustomerRequest(customer=make_customer_msg(customerid=""))

    resp = service.CreateCustomer(req, ctx)

    assert resp.ok is False
    assert resp.message == "customerid is required"
    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT


def test_create_customer_duplicate_sets_already_exists():
    from pymongo.errors import DuplicateKeyError

    fake_db = FakeCustomerDB()
    fake_db.raise_on_create = DuplicateKeyError("dup")
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    req = customer_pb2.CreateCustomerRequest(customer=make_customer_msg(customerid="C1"))

    resp = service.CreateCustomer(req, ctx)

    assert resp.ok is False
    assert resp.message == "already exists"
    assert ctx.code == grpc.StatusCode.ALREADY_EXISTS


def test_create_customer_generic_error_sets_internal():
    fake_db = FakeCustomerDB()
    fake_db.raise_on_create = RuntimeError("boom")
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    req = customer_pb2.CreateCustomerRequest(customer=make_customer_msg())

    resp = service.CreateCustomer(req, ctx)

    assert resp.ok is False
    assert resp.message == "internal error"
    assert ctx.code == grpc.StatusCode.INTERNAL
    assert ctx.details == "boom"


def test_create_customer_success():
    fake_db = FakeCustomerDB()
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    req = customer_pb2.CreateCustomerRequest(customer=make_customer_msg(customerid="C123"))

    resp = service.CreateCustomer(req, ctx)

    assert resp.ok is True
    assert resp.message == "created"
    assert fake_db.created[0]["customerid"] == "C123"


def test_get_customer_by_id_not_found_sets_not_found():
    fake_db = FakeCustomerDB()
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    req = customer_pb2.GetCustomerByIdRequest(customerid="missing")

    resp = service.GetCustomerById(req, ctx)

    assert resp.ok is False
    assert resp.message == "not found"
    assert ctx.code == grpc.StatusCode.NOT_FOUND


def test_get_customer_by_id_success():
    fake_db = FakeCustomerDB()
    customer_doc = {
        "customerid": "C1",
        "firstname": "Alice",
        "lastname": "Smith",
        "email": "alice@example.com",
        "phone": "+1-555-0000",
        "address": {
            "street": "123 Main St",
            "city": "Testville",
            "state": "TS",
            "zip": "12345",
            "country": "Testland",
        },
    }
    fake_db.by_id["C1"] = customer_doc
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    req = customer_pb2.GetCustomerByIdRequest(customerid="C1")

    resp = service.GetCustomerById(req, ctx)

    assert resp.ok is True
    assert resp.message == "ok"
    assert resp.customer.customerid == "C1"
    assert resp.customer.address.city == "Testville"


def test_update_customer_no_fields_sets_invalid_argument():
    fake_db = FakeCustomerDB()
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    empty_customer = customer_pb2.Customer(customerid="C1")
    req = customer_pb2.UpdateCustomerRequest(customerid="C1", customer=empty_customer)

    resp = service.UpdateCustomer(req, ctx)

    assert resp.ok is False
    assert resp.message == "no fields to update"
    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT


def test_update_customer_not_found_sets_not_found():
    fake_db = FakeCustomerDB()
    fake_db.update_result["C1"] = False
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    req = customer_pb2.UpdateCustomerRequest(customerid="C1", customer=make_customer_msg())

    resp = service.UpdateCustomer(req, ctx)

    assert resp.ok is False
    assert resp.message == "not found"
    assert ctx.code == grpc.StatusCode.NOT_FOUND


def test_update_customer_success():
    fake_db = FakeCustomerDB()
    fake_db.by_id["C1"] = {"customerid": "C1", "lastname": "Old"}
    fake_db.update_result["C1"] = True
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    customer_msg = make_customer_msg(lastname="NewLast")
    req = customer_pb2.UpdateCustomerRequest(customerid="C1", customer=customer_msg)

    resp = service.UpdateCustomer(req, ctx)

    assert resp.ok is True
    assert resp.message == "updated"
    assert fake_db.by_id["C1"]["lastname"] == "NewLast"


def test_delete_customer_not_found_sets_not_found():
    fake_db = FakeCustomerDB()
    fake_db.delete_result["C1"] = False
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    req = customer_pb2.DeleteCustomerRequest(customerid="C1")

    resp = service.DeleteCustomer(req, ctx)

    assert resp.ok is False
    assert resp.message == "not found"
    assert ctx.code == grpc.StatusCode.NOT_FOUND


def test_delete_customer_success():
    fake_db = FakeCustomerDB()
    fake_db.delete_result["C1"] = True
    service = make_service_with_fake_db(fake_db)
    ctx = DummyContext()

    req = customer_pb2.DeleteCustomerRequest(customerid="C1")

    resp = service.DeleteCustomer(req, ctx)

    assert resp.ok is True
    assert resp.message == "deleted"
