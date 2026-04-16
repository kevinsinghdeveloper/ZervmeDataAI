"""Unit tests for SuperAdminResourceManager."""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.models.RequestResourceModel import RequestResourceModel
from tests.conftest import make_request, SAMPLE_USER_ITEM, SAMPLE_ADMIN_USER_ITEM, SAMPLE_ORG_ITEM


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

SAMPLE_ORG_ITEM_RAW = {
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

SAMPLE_USER_ITEM_RAW = {
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


def _build_mock_db(orgs_items=None, users_items=None, user_get_item=None):
    """Build a mock db object with repo attributes."""
    mock_db = MagicMock()

    mock_db.organizations.list_all.return_value = orgs_items or []
    mock_db.organizations.count.return_value = len(orgs_items or [])
    mock_db.organizations.update.return_value = {}

    mock_db.users.list_all.return_value = users_items or []
    mock_db.users.count.return_value = len(users_items or [])
    mock_db.users.update_fields.return_value = {}

    if user_get_item is not None:
        # Return a MagicMock with dict-like attributes
        user_obj = MagicMock()
        user_obj.is_active = user_get_item.get("is_active", True)
        user_obj.id = user_get_item.get("id")
        mock_db.users.get_by_id.return_value = user_obj
    else:
        mock_db.users.get_by_id.return_value = None

    return mock_db


# ---------------------------------------------------------------------------
# GET - list_organizations
# ---------------------------------------------------------------------------

def test_list_organizations_success():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    mock_db = _build_mock_db(orgs_items=[SAMPLE_ORG_ITEM_RAW])

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list_organizations"}))

    assert resp.success is True
    assert "organizations" in resp.data
    assert resp.data["total"] == 1
    assert resp.data["organizations"][0]["name"] == "Test Org"


# ---------------------------------------------------------------------------
# GET - list_users
# ---------------------------------------------------------------------------

@patch("managers.super_admin.SuperAdminResourceManager.user_role_service")
def test_list_users_success(mock_role_svc):
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    mock_role_svc.is_super_admin.return_value = False
    mock_role_svc.get_user_org_memberships.return_value = []

    mock_db = _build_mock_db(users_items=[SAMPLE_USER_ITEM_RAW])

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list_users"}))

    assert resp.success is True
    assert "users" in resp.data
    assert resp.data["total"] == 1
    assert resp.data["users"][0]["email"] == "test@example.com"


# ---------------------------------------------------------------------------
# GET - stats
# ---------------------------------------------------------------------------

def test_stats_success():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    mock_db = MagicMock()
    mock_db.organizations.count.return_value = 3
    mock_db.users.count.return_value = 10

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "stats"}))

    assert resp.success is True
    assert resp.data["totalOrganizations"] == 3
    assert resp.data["totalUsers"] == 10


# ---------------------------------------------------------------------------
# PUT - update_organization
# ---------------------------------------------------------------------------

def test_update_org_success():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    mock_db = _build_mock_db()

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.put(make_request({
        "action": "update_organization",
        "org_id": "org-456",
        "isActive": False,
    }))

    assert resp.success is True
    assert resp.message == "Organization updated"
    mock_db.organizations.update.assert_called_once()


def test_update_org_no_fields():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    mock_db = _build_mock_db()

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.put(make_request({
        "action": "update_organization",
        "org_id": "org-456",
        # No isActive or planTier provided
    }))

    assert resp.success is False
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# PUT - toggle_user
# ---------------------------------------------------------------------------

def test_toggle_user_activate():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    inactive_user = {**SAMPLE_USER_ITEM_RAW, "is_active": False}
    mock_db = _build_mock_db(user_get_item=inactive_user)

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.put(make_request({
        "action": "toggle_user",
        "target_user_id": "user-123",
    }))

    assert resp.success is True
    assert "activated" in resp.message
    mock_db.users.update_fields.assert_called_once()


def test_toggle_user_deactivate():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    active_user = {**SAMPLE_USER_ITEM_RAW, "is_active": True}
    mock_db = _build_mock_db(user_get_item=active_user)

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.put(make_request({
        "action": "toggle_user",
        "target_user_id": "user-123",
    }))

    assert resp.success is True
    assert "deactivated" in resp.message
    mock_db.users.update_fields.assert_called_once()


# ---------------------------------------------------------------------------
# POST / DELETE - not implemented
# ---------------------------------------------------------------------------

def test_post_not_implemented():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    mock_db = MagicMock()

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "anything"}))

    assert resp.success is False
    assert resp.status_code == 405


def test_delete_not_implemented():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    mock_db = MagicMock()

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.delete(make_request({"action": "anything"}))

    assert resp.success is False
    assert resp.status_code == 405


# ---------------------------------------------------------------------------
# Invalid actions
# ---------------------------------------------------------------------------

def test_invalid_get_action():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    mock_db = MagicMock()

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_invalid_put_action():
    from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager

    mock_db = MagicMock()

    mgr = SuperAdminResourceManager(service_managers={"db": mock_db})
    resp = mgr.put(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400
