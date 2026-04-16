"""Unit tests for rbac_utils (decorators and helpers)."""
import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.rbac_utils import _role_meets_minimum, org_role_required, super_admin_required
import utils.rbac_utils as _rbac
from database.schemas.user import UserItem

# ---------------------------------------------------------------------------
# Test app for decorator testing
# ---------------------------------------------------------------------------

_app = Flask(__name__)


def _make_user_item(user_id="u-1", org_id="org-1", org_role="member", is_super_admin=False):
    return UserItem.from_item({
        "id": user_id,
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": org_role,
        "org_role": org_role,
        "org_id": org_id,
        "is_super_admin": is_super_admin,
        "is_active": True,
        "is_verified": True,
        "status": "active",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
    })


@pytest.fixture(autouse=True)
def _inject_mock_db():
    """Inject a mock db for rbac_utils._get_current_user."""
    mock_db = MagicMock()
    old = _rbac._db
    _rbac._db = mock_db
    yield mock_db
    _rbac._db = old


# ---------------------------------------------------------------------------
# _role_meets_minimum (pure function, no mocks)
# ---------------------------------------------------------------------------

class TestRoleMeetsMinimum:
    def test_member_meets_member(self):
        assert _role_meets_minimum("member", "member") is True

    def test_admin_meets_member(self):
        assert _role_meets_minimum("admin", "member") is True

    def test_owner_meets_admin(self):
        assert _role_meets_minimum("owner", "admin") is True

    def test_member_fails_admin(self):
        assert _role_meets_minimum("member", "admin") is False

    def test_manager_fails_owner(self):
        assert _role_meets_minimum("manager", "owner") is False

    def test_unknown_user_role_returns_false(self):
        assert _role_meets_minimum("unknown_role", "member") is False

    def test_unknown_min_role_returns_false(self):
        assert _role_meets_minimum("admin", "unknown_role") is False

    def test_same_role_meets(self):
        for role in ["member", "manager", "admin", "owner"]:
            assert _role_meets_minimum(role, role) is True


# ---------------------------------------------------------------------------
# org_role_required decorator
# ---------------------------------------------------------------------------

PATCH_IS_SUPER_ADMIN = "utils.rbac_utils.user_role_service.is_super_admin"
PATCH_MEETS_MIN_ROLE = "utils.rbac_utils.user_role_service.user_meets_minimum_role"


class TestOrgRoleRequired:
    def _make_decorated_view(self, *roles):
        @org_role_required(*roles)
        def view():
            return {"success": True}, 200
        return view

    @patch(PATCH_MEETS_MIN_ROLE)
    @patch(PATCH_IS_SUPER_ADMIN)
    def test_super_admin_bypasses(self, mock_is_sa, mock_meets, _inject_mock_db):
        user = _make_user_item(org_role="member")
        _inject_mock_db.users.get_by_id.return_value = user
        mock_is_sa.return_value = True

        view = self._make_decorated_view("admin", "owner")
        with _app.test_request_context("/test", headers={"X-Org-Id": "org-1"}):
            from flask import request
            request.user_id = "u-1"
            result, status = view()
            assert status == 200
            assert result["success"] is True
            mock_meets.assert_not_called()

    @patch(PATCH_MEETS_MIN_ROLE)
    @patch(PATCH_IS_SUPER_ADMIN)
    def test_member_blocked_from_admin_route(self, mock_is_sa, mock_meets, _inject_mock_db):
        user = _make_user_item(org_role="member")
        _inject_mock_db.users.get_by_id.return_value = user
        mock_is_sa.return_value = False
        mock_meets.return_value = False

        view = self._make_decorated_view("admin", "owner")
        with _app.test_request_context("/test", headers={"X-Org-Id": "org-1"}):
            from flask import request
            request.user_id = "u-1"
            resp = view()
            data = json.loads(resp[0].data)
            assert resp[1] == 403
            assert data["error"] == "Insufficient permissions"

    @patch(PATCH_MEETS_MIN_ROLE)
    @patch(PATCH_IS_SUPER_ADMIN)
    def test_admin_allowed_for_manager_route(self, mock_is_sa, mock_meets, _inject_mock_db):
        user = _make_user_item(org_role="admin")
        _inject_mock_db.users.get_by_id.return_value = user
        mock_is_sa.return_value = False
        mock_meets.return_value = True

        view = self._make_decorated_view("manager")
        with _app.test_request_context("/test", headers={"X-Org-Id": "org-1"}):
            from flask import request
            request.user_id = "u-1"
            result, status = view()
            assert status == 200

    @patch(PATCH_MEETS_MIN_ROLE)
    @patch(PATCH_IS_SUPER_ADMIN)
    def test_missing_org_id_returns_400(self, mock_is_sa, mock_meets, _inject_mock_db):
        # User with no org_id and no X-Org-Id header
        user = _make_user_item(org_id="")
        _inject_mock_db.users.get_by_id.return_value = user
        mock_is_sa.return_value = False

        view = self._make_decorated_view("admin")
        with _app.test_request_context("/test"):
            from flask import request
            request.user_id = "u-1"
            resp = view()
            data = json.loads(resp[0].data)
            assert resp[1] == 400
            assert "Organization context required" in data["error"]

    @patch(PATCH_IS_SUPER_ADMIN)
    def test_user_not_found_returns_404(self, mock_is_sa, _inject_mock_db):
        _inject_mock_db.users.get_by_id.return_value = None

        view = self._make_decorated_view("admin")
        with _app.test_request_context("/test"):
            from flask import request
            request.user_id = "nonexistent"
            resp = view()
            data = json.loads(resp[0].data)
            assert resp[1] == 404


# ---------------------------------------------------------------------------
# super_admin_required decorator
# ---------------------------------------------------------------------------

class TestSuperAdminRequired:
    @patch(PATCH_IS_SUPER_ADMIN)
    def test_allows_super_admin(self, mock_is_sa, _inject_mock_db):
        user = _make_user_item(is_super_admin=True)
        _inject_mock_db.users.get_by_id.return_value = user
        mock_is_sa.return_value = True

        @super_admin_required
        def view():
            return {"success": True}, 200

        with _app.test_request_context("/test"):
            from flask import request
            request.user_id = "u-1"
            result, status = view()
            assert status == 200

    @patch(PATCH_IS_SUPER_ADMIN)
    def test_blocks_non_super_admin(self, mock_is_sa, _inject_mock_db):
        user = _make_user_item(is_super_admin=False)
        _inject_mock_db.users.get_by_id.return_value = user
        mock_is_sa.return_value = False

        @super_admin_required
        def view():
            return {"success": True}, 200

        with _app.test_request_context("/test"):
            from flask import request
            request.user_id = "u-1"
            resp = view()
            data = json.loads(resp[0].data)
            assert resp[1] == 403
            assert "Super admin" in data["error"]

    @patch(PATCH_IS_SUPER_ADMIN)
    def test_user_not_found_returns_404(self, mock_is_sa, _inject_mock_db):
        _inject_mock_db.users.get_by_id.return_value = None

        @super_admin_required
        def view():
            return {"success": True}, 200

        with _app.test_request_context("/test"):
            from flask import request
            request.user_id = "nonexistent"
            resp = view()
            data = json.loads(resp[0].data)
            assert resp[1] == 404
