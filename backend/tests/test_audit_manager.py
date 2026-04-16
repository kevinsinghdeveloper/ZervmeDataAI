"""Unit tests for AuditResourceManager."""
import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.models.RequestResourceModel import RequestResourceModel
from managers.audit.AuditResourceManager import AuditResourceManager
from tests.conftest import make_request, SAMPLE_ADMIN_USER_ITEM, SAMPLE_USER_ITEM


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

SAMPLE_AUDIT_LOG_1 = {
    "id": "log-1",
    "user_id": "user-123",
    "action": "user_login",
    "resource": "auth",
    "resource_id": None,
    "details": "{}",
    "ip_address": "127.0.0.1",
    "timestamp": "2024-01-15T10:00:00",
    "org_id": None,
}

SAMPLE_AUDIT_LOG_2 = {
    "id": "log-2",
    "user_id": "user-456",
    "action": "project_created",
    "resource": "projects",
    "resource_id": "proj-1",
    "details": '{"name": "New Project"}',
    "ip_address": "192.168.1.1",
    "timestamp": "2024-01-16T14:30:00",
    "org_id": "org-456",
}


def _make_user_obj(item):
    """Create a mock user object from a dict."""
    if item is None:
        return None
    obj = MagicMock()
    for k, v in item.items():
        setattr(obj, k, v)
    return obj


ADMIN_USER_OBJ = _make_user_obj({**SAMPLE_ADMIN_USER_ITEM, "id": "admin-789", "is_super_admin": True})
NON_ADMIN_USER_OBJ = _make_user_obj({**SAMPLE_USER_ITEM, "id": "user-123", "is_super_admin": False})


def _build_mock_db(user_obj=None, audit_items=None, audit_get_item=None):
    """Build a mock db service with preconfigured repos."""
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj

    # raw_scan for audit_logs: return items with no LastEvaluatedKey to exit loop
    mock_db.audit_logs.raw_scan.return_value = {
        "Items": audit_items or [],
        "Count": len(audit_items or []),
    }
    # raw_query for get_log (composite key: id + timestamp)
    mock_db.audit_logs.raw_query.return_value = {
        "Items": [audit_get_item] if audit_get_item else [],
    }

    return mock_db


# ---------------------------------------------------------------------------
# GET - list_logs (admin success)
# ---------------------------------------------------------------------------

def test_list_logs_success():
    mock_db = _build_mock_db(
        user_obj=ADMIN_USER_OBJ,
        audit_items=[SAMPLE_AUDIT_LOG_1, SAMPLE_AUDIT_LOG_2],
    )

    mgr = AuditResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list_logs"}, user_id="admin-789"))

    assert resp.success is True
    assert "logs" in resp.data
    assert resp.data["total"] == 2
    assert resp.data["page"] == 1
    assert resp.data["perPage"] == 50


# ---------------------------------------------------------------------------
# GET - list_logs (non-admin rejected)
# ---------------------------------------------------------------------------

def test_list_logs_non_admin():
    mock_db = _build_mock_db(user_obj=NON_ADMIN_USER_OBJ)

    mgr = AuditResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list_logs"}, user_id="user-123"))

    assert resp.success is False
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET - list_logs with filters
# ---------------------------------------------------------------------------

def test_list_logs_with_filters():
    mock_db = _build_mock_db(
        user_obj=ADMIN_USER_OBJ,
        audit_items=[SAMPLE_AUDIT_LOG_1],
    )

    mgr = AuditResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({
        "action": "list_logs",
        "action_filter": "user_login",
        "user_filter": "user-123",
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-12-31T23:59:59",
    }, user_id="admin-789"))

    assert resp.success is True
    assert resp.data["total"] == 1

    # Verify raw_scan was called with filter expressions
    call_kwargs = mock_db.audit_logs.raw_scan.call_args
    assert "FilterExpression" in call_kwargs.kwargs or "FilterExpression" in (call_kwargs[1] if len(call_kwargs) > 1 else {})


# ---------------------------------------------------------------------------
# GET - list_logs empty result
# ---------------------------------------------------------------------------

def test_list_logs_empty():
    mock_db = _build_mock_db(user_obj=ADMIN_USER_OBJ, audit_items=[])

    mgr = AuditResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list_logs"}, user_id="admin-789"))

    assert resp.success is True
    assert resp.data["logs"] == []
    assert resp.data["total"] == 0


# ---------------------------------------------------------------------------
# GET - get_log (admin success)
# ---------------------------------------------------------------------------

def test_get_log_success():
    mock_db = _build_mock_db(
        user_obj=ADMIN_USER_OBJ,
        audit_get_item=SAMPLE_AUDIT_LOG_1,
    )

    mgr = AuditResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request(
        {"action": "get_log", "log_id": "log-1"},
        user_id="admin-789",
    ))

    assert resp.success is True
    assert resp.data["id"] == "log-1"
    assert resp.data["action"] == "user_login"
    assert resp.data["userId"] == "user-123"


# ---------------------------------------------------------------------------
# GET - get_log not found
# ---------------------------------------------------------------------------

def test_get_log_not_found():
    mock_db = _build_mock_db(user_obj=ADMIN_USER_OBJ, audit_get_item=None)

    mgr = AuditResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request(
        {"action": "get_log", "log_id": "nonexistent"},
        user_id="admin-789",
    ))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET - get_log (non-admin rejected)
# ---------------------------------------------------------------------------

def test_get_log_non_admin():
    mock_db = _build_mock_db(user_obj=NON_ADMIN_USER_OBJ, audit_get_item=SAMPLE_AUDIT_LOG_1)

    mgr = AuditResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request(
        {"action": "get_log", "log_id": "log-1"},
        user_id="user-123",
    ))

    assert resp.success is False
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST / PUT / DELETE - not supported
# ---------------------------------------------------------------------------

def test_post_not_supported():
    mgr = AuditResourceManager()
    resp = mgr.post(make_request({"action": "anything"}))

    assert resp.success is False
    assert resp.status_code == 405


def test_put_not_supported():
    mgr = AuditResourceManager()
    resp = mgr.put(make_request({"action": "anything"}))

    assert resp.success is False
    assert resp.status_code == 405


def test_delete_not_supported():
    mgr = AuditResourceManager()
    resp = mgr.delete(make_request({"action": "anything"}))

    assert resp.success is False
    assert resp.status_code == 405
