"""Unit tests for OrganizationResourceManager."""
import pytest
from unittest.mock import patch, MagicMock

from managers.organizations.OrganizationResourceManager import OrganizationResourceManager
from database.schemas.user import UserItem
from tests.conftest import make_request, SAMPLE_USER_ITEM, SAMPLE_ORG_ITEM

_PATCH_ROLE_SVC = "managers.organizations.OrganizationResourceManager.user_role_service"


def _build_manager(user_item=None):
    """Build OrganizationResourceManager with mock db."""
    mock_db = MagicMock()

    # users.get_by_id returns UserItem
    if user_item is not None:
        mock_db.users.get_by_id.return_value = UserItem.from_item(user_item)
    else:
        mock_db.users.get_by_id.return_value = None

    # Default returns for all repos
    mock_db.organizations.raw_get_item.return_value = None
    mock_db.organizations.create.return_value = None
    mock_db.organizations.raw_update_item.return_value = None
    mock_db.organizations.batch_get_by_ids.return_value = []
    mock_db.org_invitations.raw_query.return_value = {"Items": []}
    mock_db.org_invitations.create.return_value = None
    mock_db.org_invitations.delete.return_value = True
    mock_db.users.raw_update_item.return_value = None
    mock_db.users.raw_query.return_value = {"Items": []}
    mock_db.users.raw_scan.return_value = {"Items": [], "Count": 0}
    mock_db.users.batch_get_by_ids.return_value = []

    mgr = OrganizationResourceManager(service_managers={"db": mock_db})
    return mgr, mock_db


# ===========================================================================
# GET CURRENT ORG
# ===========================================================================

class TestGetCurrentOrg:

    def test_get_current_success(self):
        mgr, mock_db = _build_manager(user_item=SAMPLE_USER_ITEM)
        mock_db.organizations.raw_get_item.return_value = SAMPLE_ORG_ITEM.copy()

        req = make_request(data={"action": "get_current"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert "organization" in resp.data
        assert resp.data["organization"]["id"] == "org-456"

    def test_get_current_no_org(self):
        no_org_user = {k: v for k, v in SAMPLE_USER_ITEM.items() if k != "org_id"}
        mgr, _ = _build_manager(user_item=no_org_user)

        req = make_request(data={"action": "get_current"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 404


# ===========================================================================
# CREATE ORG
# ===========================================================================

class TestCreateOrg:

    @patch(_PATCH_ROLE_SVC)
    def test_create_org_success(self, mock_role_svc):
        mgr, mock_db = _build_manager()

        req = make_request(data={"action": "create", "name": "My Org"}, user_id="user-123")
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert resp.data["organization"]["name"] == "My Org"
        mock_role_svc.grant_role.assert_called_once()

    def test_create_org_missing_name(self):
        mgr, _ = _build_manager()

        req = make_request(data={"action": "create", "name": ""}, user_id="user-123")
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "required" in resp.error.lower()


# ===========================================================================
# LIST MEMBERS
# ===========================================================================

class TestListMembers:

    @patch(_PATCH_ROLE_SVC)
    def test_list_members_success(self, mock_role_svc):
        mgr, mock_db = _build_manager(user_item=SAMPLE_USER_ITEM)

        from database.schemas.user_role import UserRoleItem
        mock_role_item = UserRoleItem(
            user_id="user-123", org_role="org-456#member",
            org_id="org-456", role="member",
        )
        mock_role_svc.get_org_members.return_value = [mock_role_item]

        # batch_get_by_ids returns UserItem objects in the real repo,
        # but the manager iterates and calls UserItem.from_item() on each.
        # Since we're mocking, return raw dicts that from_item can handle.
        mock_db.users.batch_get_by_ids.return_value = [SAMPLE_USER_ITEM.copy()]

        req = make_request(data={"action": "list_members"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert "members" in resp.data


# ===========================================================================
# LIST INVITATIONS
# ===========================================================================

class TestListInvitations:

    def test_list_invitations_success(self):
        mgr, mock_db = _build_manager(user_item=SAMPLE_USER_ITEM)

        inv_item = {
            "id": "inv-1",
            "org_id": "org-456",
            "email": "invite@example.com",
            "role": "member",
            "token": "tok-abc",
            "status": "pending",
            "invited_by": "user-123",
            "expires_at": "2099-01-01T00:00:00",
            "expires_at_ttl": 9999999999,
            "created_at": "2024-01-01T00:00:00",
        }
        mock_db.org_invitations.raw_query.return_value = {"Items": [inv_item]}

        req = make_request(data={"action": "list_invitations"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is True
        assert "invitations" in resp.data
        assert len(resp.data["invitations"]) == 1


# ===========================================================================
# CREATE INVITATION
# ===========================================================================

class TestCreateInvitation:

    def test_create_invitation_success(self):
        mgr, mock_db = _build_manager(user_item=SAMPLE_USER_ITEM)

        req = make_request(
            data={"action": "create_invitation", "email": "new@example.com", "role": "member"},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert "invitation" in resp.data

    def test_create_invitation_no_email(self):
        mgr, _ = _build_manager(user_item=SAMPLE_USER_ITEM)

        req = make_request(
            data={"action": "create_invitation", "email": ""},
            user_id="user-123",
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "required" in resp.error.lower()


# ===========================================================================
# UPDATE CURRENT ORG
# ===========================================================================

class TestUpdateCurrentOrg:

    def test_update_current_success(self):
        mgr, mock_db = _build_manager(user_item=SAMPLE_USER_ITEM)

        req = make_request(
            data={"action": "update_current", "name": "Renamed Org"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        mock_db.organizations.raw_update_item.assert_called_once()

    def test_update_current_no_fields(self):
        mgr, _ = _build_manager(user_item=SAMPLE_USER_ITEM)

        req = make_request(
            data={"action": "update_current"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 400


# ===========================================================================
# UPDATE MEMBER ROLE
# ===========================================================================

class TestUpdateMemberRole:

    @patch(_PATCH_ROLE_SVC)
    def test_update_member_role(self, mock_role_svc):
        mgr, mock_db = _build_manager(user_item=SAMPLE_USER_ITEM)

        req = make_request(
            data={"action": "update_member_role", "member_id": "member-1", "role": "admin"},
            user_id="user-123",
        )
        resp = mgr.put(req)

        assert resp.success is True
        assert "updated" in resp.message.lower()


# ===========================================================================
# DELETE INVITATION
# ===========================================================================

class TestDeleteInvitation:

    def test_delete_invitation(self):
        mgr, mock_db = _build_manager(user_item=SAMPLE_USER_ITEM)

        req = make_request(
            data={"action": "delete_invitation", "invitation_id": "inv-1"},
            user_id="user-123",
        )
        resp = mgr.delete(req)

        assert resp.success is True
        assert "deleted" in resp.message.lower()


# ===========================================================================
# REMOVE MEMBER
# ===========================================================================

class TestRemoveMember:

    @patch(_PATCH_ROLE_SVC)
    def test_remove_member(self, mock_role_svc):
        mgr, mock_db = _build_manager(user_item=SAMPLE_USER_ITEM)

        req = make_request(
            data={"action": "remove_member", "member_id": "member-1"},
            user_id="user-123",
        )
        resp = mgr.delete(req)

        assert resp.success is True
        assert "removed" in resp.message.lower()


# ===========================================================================
# INVALID ACTION
# ===========================================================================

class TestOrgActionRouting:

    def test_invalid_get_action(self):
        mgr, _ = _build_manager()

        req = make_request(data={"action": "nonexistent"}, user_id="user-123")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 400
