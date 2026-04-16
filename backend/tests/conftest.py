"""Shared test fixtures for backend unit tests."""
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "postgres: tests requiring a running PostgreSQL instance")


# ---------------------------------------------------------------------------
# Flask app + request context -- keeps flask.request happy during tests
# ---------------------------------------------------------------------------

_test_app = Flask(__name__)


@pytest.fixture(autouse=True)
def flask_request_context():
    """Provide a Flask request context for every test automatically.

    Many managers reference ``flask.request.remote_addr`` for audit logging.
    Without an active request context the werkzeug LocalProxy raises
    RuntimeError when ``@patch`` inspects the attribute.
    """
    with _test_app.test_request_context("/test", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
        yield


# ---------------------------------------------------------------------------
# DynamoDB table mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_table():
    """Returns a MagicMock DynamoDB table."""
    table = MagicMock()
    table.get_item.return_value = {"Item": None}
    table.put_item.return_value = {}
    table.update_item.return_value = {}
    table.delete_item.return_value = {}
    table.query.return_value = {"Items": []}
    table.scan.return_value = {"Items": [], "Count": 0}
    return table


@pytest.fixture
def mock_tables():
    """Returns a dict of mock tables, keyed by table name."""
    tables = {}
    def _get_table(name):
        if name not in tables:
            tables[name] = MagicMock()
            tables[name].get_item.return_value = {"Item": None}
            tables[name].put_item.return_value = {}
            tables[name].update_item.return_value = {}
            tables[name].delete_item.return_value = {}
            tables[name].query.return_value = {"Items": []}
            tables[name].scan.return_value = {"Items": [], "Count": 0}
        return tables[name]
    return _get_table, tables


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(data=None, user_id="user-123"):
    """Helper to build a RequestResourceModel."""
    return RequestResourceModel(data=data or {}, user_id=user_id)


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

SAMPLE_USER_ITEM = {
    "id": "user-123",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "role": "member",
    "org_role": "member",
    "org_id": "org-456",
    "is_super_admin": False,
    "is_active": True,
    "is_verified": True,
    "status": "active",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

SAMPLE_ADMIN_USER_ITEM = {
    **SAMPLE_USER_ITEM,
    "id": "admin-789",
    "email": "admin@example.com",
    "role": "admin",
    "org_role": "owner",
    "is_super_admin": True,
}

SAMPLE_ORG_ITEM = {
    "id": "org-456",
    "name": "Test Org",
    "slug": "test-org",
    "owner_id": "user-123",
    "member_count": 5,
    "plan_tier": "professional",
    "is_active": True,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}
