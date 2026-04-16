"""Unit tests for UserResourceManager."""
import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import make_request, SAMPLE_USER_ITEM, SAMPLE_ADMIN_USER_ITEM

_PATCH_ROLE_SVC = "managers.users.UserResourceManager.user_role_service"


def _build_manager(mock_db=None):
    """Instantiate UserResourceManager with a mock db wired up."""
    from managers.users.UserResourceManager import UserResourceManager

    if mock_db is None:
        mock_db = MagicMock()
    mgr = UserResourceManager(service_managers={"db": mock_db})
    return mgr


# ===========================================================================
# GET CURRENT USER
# ===========================================================================

class TestGetCurrentUser:

    @patch(_PATCH_ROLE_SVC)
    def test_get_current_user_success(self, mock_role_svc):
        mock_db = MagicMock()
        mock_db.users.get_by_id.return_value = SAMPLE_USER_ITEM.copy()

        mock_role_svc.is_super_admin.return_value = False
        mock_role_svc.get_user_org_memberships.return_value = []

        mgr = _build_manager(mock_db)

        req = make_request(data={"action": "get_current_user"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["id"] == "user-123"
        assert resp.data["email"] == "test@example.com"

    def test_get_current_user_not_found(self):
        mock_db = MagicMock()
        mock_db.users.get_by_id.return_value = None

        mgr = _build_manager(mock_db)

        req = make_request(data={"action": "get_current_user"}, user_id="nonexistent")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 404


# ===========================================================================
# LIST USERS
# ===========================================================================

class TestListUsers:

    @patch(_PATCH_ROLE_SVC)
    def test_list_users_success(self, mock_role_svc):
        mock_db = MagicMock()
        mock_db.users.list_all.return_value = [
            SAMPLE_USER_ITEM.copy(),
            SAMPLE_ADMIN_USER_ITEM.copy(),
        ]

        mock_role_svc.is_super_admin.return_value = True

        mgr = _build_manager(mock_db)

        req = make_request(data={"action": "list_users"}, user_id="admin-789")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "users" in resp.data
        assert resp.data["total"] == 2
        assert resp.data["page"] == 1

    @patch(_PATCH_ROLE_SVC)
    def test_list_users_non_admin(self, mock_role_svc):
        mock_db = MagicMock()

        mock_role_svc.is_super_admin.return_value = False

        mgr = _build_manager(mock_db)

        req = make_request(data={"action": "list_users"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 403
        assert "admin" in resp.error.lower()


# ===========================================================================
# UPDATE USER
# ===========================================================================

class TestUpdateUser:

    def test_update_user_self_success(self):
        mock_db = MagicMock()

        user_item = SAMPLE_USER_ITEM.copy()
        updated_item = {**user_item, "first_name": "Updated"}
        mock_db.users.get_by_id.side_effect = [
            user_item,      # requesting user lookup
            user_item,      # target user check
            updated_item,   # return updated user
        ]
        mock_db.users.update_fields.return_value = {}

        mgr = _build_manager(mock_db)

        req = make_request(
            data={"action": "update_user", "target_user_id": "user-123", "firstName": "Updated"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert resp.data["firstName"] == "Updated"

    @patch(_PATCH_ROLE_SVC)
    def test_update_user_unauthorized(self, mock_role_svc):
        mock_db = MagicMock()
        mock_db.users.get_by_id.return_value = SAMPLE_USER_ITEM.copy()

        mock_role_svc.is_super_admin.return_value = False

        mgr = _build_manager(mock_db)

        req = make_request(
            data={"action": "update_user", "target_user_id": "other-user-999", "firstName": "Hacked"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 403


# ===========================================================================
# UPDATE ROLE
# ===========================================================================

class TestUpdateRole:

    @patch(_PATCH_ROLE_SVC)
    def test_update_role_success(self, mock_role_svc):
        mock_db = MagicMock()

        mock_role_svc.is_super_admin.return_value = True

        target_item = SAMPLE_USER_ITEM.copy()
        updated_item = {**target_item, "role": "editor"}

        mock_db.users.get_by_id.side_effect = [
            target_item,    # target user before update
            updated_item,   # target user after update
        ]
        mock_db.users.update_fields.return_value = {}
        mock_db.audit_logs.create.return_value = {}

        mgr = _build_manager(mock_db)

        req = make_request(
            data={"action": "update_role", "target_user_id": "user-123", "role": "editor"},
            user_id="admin-789",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert "editor" in resp.message.lower()

    def test_update_role_invalid(self):
        mock_db = MagicMock()
        mgr = _build_manager(mock_db)

        req = make_request(
            data={"action": "update_role", "target_user_id": "user-123", "role": "superuser"},
            user_id="admin-789",
        )
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "invalid role" in resp.error.lower()


# ===========================================================================
# DELETE USER
# ===========================================================================

class TestDeleteUser:

    @patch(_PATCH_ROLE_SVC)
    def test_delete_user_not_admin(self, mock_role_svc):
        mock_db = MagicMock()
        mock_db.users.get_by_id.return_value = SAMPLE_USER_ITEM.copy()

        mock_role_svc.is_super_admin.return_value = False

        mgr = _build_manager(mock_db)

        req = make_request(
            data={"action": "delete_user", "target_user_id": "other-user"},
            user_id="user-123",
        )
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 403


# ===========================================================================
# METHOD NOT SUPPORTED / UNKNOWN ACTION
# ===========================================================================

class TestUserMethodRouting:

    def test_post_not_supported(self):
        mgr = _build_manager()

        req = make_request(data={"action": "create"}, user_id="user-123")
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 405

    def test_invalid_get_action(self):
        mgr = _build_manager()

        req = make_request(data={"action": "nonexistent"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 400
