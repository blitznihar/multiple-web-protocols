"""Tests for soap.customer_service.CustomerSoapService."""

from unittest.mock import Mock
import pytest
from soap.customer_service import CustomerSoapService, Customer


class MockCustomerDB:
    def __init__(self):
        self.customers = {}

    def create_customer(self, customer):
        customerid = customer["customerid"]
        self.customers[customerid] = customer
        return f"mock_id_{customerid}"

    def get_customer_by_id(self, customerid):
        return self.customers.get(customerid)

    def update_customer(self, customerid, updates):
        if customerid in self.customers:
            self.customers[customerid].update(updates)
            return True
        return False

    def delete_customer(self, customerid):
        if customerid in self.customers:
            del self.customers[customerid]
            return True
        return False


@pytest.fixture
def mock_db():
    return MockCustomerDB()


@pytest.fixture
def service(mock_db):
    service_instance = CustomerSoapService()
    CustomerSoapService.db = mock_db  # Set class attribute
    return service_instance


def test_create_customer(service, mock_db):
    ctx = Mock()
    ctx.descriptor.service_class.db = mock_db
    result = service.create_customer(ctx, "123", "John Doe", "john@example.com", 30)
    assert result == "mock_id_123"
    assert "123" in mock_db.customers


def test_get_customer_existing(service, mock_db):
    mock_db.customers["456"] = {
        "customerid": "456",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "age": 25,
    }
    ctx = Mock()
    ctx.descriptor.service_class.db = mock_db
    result = service.get_customer(ctx, "456")
    assert isinstance(result, Customer)
    assert result.customerid == "456"


def test_get_customer_nonexistent(service, mock_db):
    ctx = Mock()
    ctx.descriptor.service_class.db = mock_db
    result = service.get_customer(ctx, "nonexistent")
    assert result is None


def test_update_customer_email_success(service, mock_db):
    mock_db.customers["789"] = {
        "customerid": "789",
        "name": "Bob Smith",
        "email": "bob@example.com",
        "age": 40,
    }
    ctx = Mock()
    ctx.descriptor.service_class.db = mock_db
    result = service.update_customer_email(ctx, "789", "bob.new@example.com")
    assert result is True
    assert mock_db.customers["789"]["email"] == "bob.new@example.com"


def test_update_customer_email_nonexistent(service, mock_db):
    ctx = Mock()
    ctx.descriptor.service_class.db = mock_db
    result = service.update_customer_email(ctx, "nonexistent", "new@example.com")
    assert result is False


def test_delete_customer_success(service, mock_db):
    mock_db.customers["101"] = {
        "customerid": "101",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "age": 35,
    }
    ctx = Mock()
    ctx.descriptor.service_class.db = mock_db
    result = service.delete_customer(ctx, "101")
    assert result is True
    assert "101" not in mock_db.customers


def test_delete_customer_nonexistent(service, mock_db):
    ctx = Mock()
    ctx.descriptor.service_class.db = mock_db
    result = service.delete_customer(ctx, "nonexistent")
    assert result is False
