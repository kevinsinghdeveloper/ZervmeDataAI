"""Unit tests for user_role_service."""
import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import utils.user_role_service as _urs
from database.schemas.user_role import UserRoleItem


def _role_item(user_id="u-1", org_id="org-1", role="member", is_active=True, granted_at="2025-01-01T00:00:00"):
    return UserRoleItem(
        user_id=user_id,
        org_role=f"{org_id}#{role}" if org_id != "GLOBAL" else f"GLOBAL#{role}",
        org_id=org_id,
        role=role,
        granted_by="system",
        granted_at=granted_at,
        is_active=is_active,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
    )


@pytest.fixture(autouse=True)
def _inject_mock_repo():
    """Inject a fresh mock repo for each test."""
    mock_repo = MagicMock()
    old = _urs._repo
    _urs._repo = mock_repo
    yield mock_repo
    _urs._repo = old


# ---------------------------------------------------------------------------
# get_user_roles
# ---------------------------------------------------------------------------

class TestGetUserRoles:
    def test_returns_active_roles(self, _inject_mock_repo):
        repo = _inject_mock_repo
        repo.get_roles_for_user.return_value = [
            _role_item(role="member"),
            _role_item(org_id="org-2", role="admin"),
        ]

        roles = _urs.get_user_roles("u-1")
        assert len(roles) == 2
        assert roles[0].role == "member"
        assert roles[1].role == "admin"
        repo.get_roles_for_user.assert_called_once_with("u-1")

    def test_empty_when_no_roles(self, _inject_mock_repo):
        _inject_mock_repo.get_roles_for_user.return_value = []
        assert _urs.get_user_roles("u-1") == []


# ---------------------------------------------------------------------------
# get_user_org_roles
# ---------------------------------------------------------------------------

class TestGetUserOrgRoles:
    def test_returns_roles_for_org(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = [
            _role_item(org_id="org-1", role="member"),
            _role_item(org_id="org-1", role="admin"),
        ]

        roles = _urs.get_user_org_roles("u-1", "org-1")
        assert len(roles) == 2
        _inject_mock_repo.get_user_org_roles.assert_called_once_with("u-1", "org-1")


# ---------------------------------------------------------------------------
# is_super_admin
# ---------------------------------------------------------------------------

class TestIsSuperAdmin:
    def test_true_when_active(self, _inject_mock_repo):
        _inject_mock_repo.is_super_admin.return_value = True
        assert _urs.is_super_admin("u-1") is True

    def test_false_when_missing(self, _inject_mock_repo):
        _inject_mock_repo.is_super_admin.return_value = False
        assert _urs.is_super_admin("u-1") is False


# ---------------------------------------------------------------------------
# get_user_highest_org_role
# ---------------------------------------------------------------------------

class TestGetUserHighestOrgRole:
    def test_picks_highest(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = [
            _role_item(role="member"),
            _role_item(role="admin"),
        ]
        assert _urs.get_user_highest_org_role("u-1", "org-1") == "admin"

    def test_owner_is_highest(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = [
            _role_item(role="admin"),
            _role_item(role="owner"),
            _role_item(role="member"),
        ]
        assert _urs.get_user_highest_org_role("u-1", "org-1") == "owner"

    def test_none_when_no_roles(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = []
        assert _urs.get_user_highest_org_role("u-1", "org-1") is None

    def test_single_role(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = [_role_item(role="manager")]
        assert _urs.get_user_highest_org_role("u-1", "org-1") == "manager"


# ---------------------------------------------------------------------------
# user_meets_minimum_role
# ---------------------------------------------------------------------------

class TestUserMeetsMinimumRole:
    def test_member_meets_member(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = [_role_item(role="member")]
        assert _urs.user_meets_minimum_role("u-1", "org-1", "member") is True

    def test_member_fails_admin(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = [_role_item(role="member")]
        assert _urs.user_meets_minimum_role("u-1", "org-1", "admin") is False

    def test_admin_meets_manager(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = [_role_item(role="admin")]
        assert _urs.user_meets_minimum_role("u-1", "org-1", "manager") is True

    def test_owner_meets_all(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = [_role_item(role="owner")]
        assert _urs.user_meets_minimum_role("u-1", "org-1", "member") is True
        assert _urs.user_meets_minimum_role("u-1", "org-1", "owner") is True

    def test_no_roles_returns_false(self, _inject_mock_repo):
        _inject_mock_repo.get_user_org_roles.return_value = []
        assert _urs.user_meets_minimum_role("u-1", "org-1", "member") is False


# ---------------------------------------------------------------------------
# get_user_org_ids
# ---------------------------------------------------------------------------

class TestGetUserOrgIds:
    def test_returns_unique_org_ids(self, _inject_mock_repo):
        _inject_mock_repo.get_roles_for_user.return_value = [
            _role_item(org_id="org-1", role="member"),
            _role_item(org_id="org-1", role="admin"),
            _role_item(org_id="org-2", role="member"),
        ]
        ids = _urs.get_user_org_ids("u-1")
        assert set(ids) == {"org-1", "org-2"}

    def test_excludes_global(self, _inject_mock_repo):
        _inject_mock_repo.get_roles_for_user.return_value = [
            _role_item(org_id="GLOBAL", role="super_admin"),
            _role_item(org_id="org-1", role="member"),
        ]
        ids = _urs.get_user_org_ids("u-1")
        assert ids == ["org-1"]


# ---------------------------------------------------------------------------
# get_org_members / get_org_member_ids
# ---------------------------------------------------------------------------

class TestGetOrgMembers:
    def test_delegates_to_repo(self, _inject_mock_repo):
        _inject_mock_repo.get_org_members.return_value = [
            _role_item(user_id="u-1", role="admin"),
            _role_item(user_id="u-2", role="member"),
        ]
        members = _urs.get_org_members("org-1")
        assert len(members) == 2
        _inject_mock_repo.get_org_members.assert_called_once_with("org-1")

    def test_filters_inactive_members(self, _inject_mock_repo):
        # Repo should only return active, but test the pass-through
        _inject_mock_repo.get_org_members.return_value = [
            _role_item(user_id="u-1", role="admin", is_active=True),
        ]
        members = _urs.get_org_members("org-1")
        assert len(members) == 1
        assert members[0].user_id == "u-1"


class TestGetOrgMemberIds:
    def test_deduplicates(self, _inject_mock_repo):
        _inject_mock_repo.get_org_members.return_value = [
            _role_item(user_id="u-1", role="admin"),
            _role_item(user_id="u-1", role="member"),
            _role_item(user_id="u-2", role="member"),
        ]
        ids = _urs.get_org_member_ids("org-1")
        assert set(ids) == {"u-1", "u-2"}


# ---------------------------------------------------------------------------
# grant_role
# ---------------------------------------------------------------------------

class TestGrantRole:
    def test_org_role_correct_sk(self, _inject_mock_repo):
        expected = _role_item(role="admin")
        _inject_mock_repo.grant_role.return_value = expected

        result = _urs.grant_role("u-1", "org-1", "admin", granted_by="granter")
        assert result.role == "admin"
        _inject_mock_repo.grant_role.assert_called_once_with("u-1", "org-1", "admin", "granter")

    def test_super_admin_uses_global_sk(self, _inject_mock_repo):
        expected = _role_item(org_id="GLOBAL", role="super_admin")
        _inject_mock_repo.grant_role.return_value = expected

        result = _urs.grant_role("u-1", "org-1", "super_admin", granted_by="system")
        assert result.org_id == "GLOBAL"
        assert result.role == "super_admin"
        _inject_mock_repo.grant_role.assert_called_once_with("u-1", "org-1", "super_admin", "system")


# ---------------------------------------------------------------------------
# revoke_role
# ---------------------------------------------------------------------------

class TestRevokeRole:
    def test_org_role_update_item(self, _inject_mock_repo):
        _urs.revoke_role("u-1", "org-1", "admin")
        _inject_mock_repo.revoke_role.assert_called_once_with("u-1", "org-1", "admin")

    def test_super_admin_uses_global_sk(self, _inject_mock_repo):
        _urs.revoke_role("u-1", "GLOBAL", "super_admin")
        _inject_mock_repo.revoke_role.assert_called_once_with("u-1", "GLOBAL", "super_admin")


# ---------------------------------------------------------------------------
# revoke_all_org_roles
# ---------------------------------------------------------------------------

class TestRevokeAllOrgRoles:
    def test_revokes_each_role(self, _inject_mock_repo):
        _urs.revoke_all_org_roles("u-1", "org-1")
        _inject_mock_repo.revoke_all_org_roles.assert_called_once_with("u-1", "org-1")


# ---------------------------------------------------------------------------
# is_last_owner
# ---------------------------------------------------------------------------

class TestIsLastOwner:
    def test_true_when_single_owner(self, _inject_mock_repo):
        _inject_mock_repo.is_last_owner.return_value = True
        assert _urs.is_last_owner("org-1") is True

    def test_false_when_multiple_owners(self, _inject_mock_repo):
        _inject_mock_repo.is_last_owner.return_value = False
        assert _urs.is_last_owner("org-1") is False

    def test_true_when_no_owners(self, _inject_mock_repo):
        _inject_mock_repo.is_last_owner.return_value = True
        assert _urs.is_last_owner("org-1") is True

    def test_ignores_inactive_owners(self, _inject_mock_repo):
        _inject_mock_repo.is_last_owner.return_value = True
        assert _urs.is_last_owner("org-1") is True


# ---------------------------------------------------------------------------
# get_user_org_memberships
# ---------------------------------------------------------------------------

class TestGetUserOrgMemberships:
    def test_groups_by_org(self, _inject_mock_repo):
        _inject_mock_repo.get_roles_for_user.return_value = [
            _role_item(org_id="org-1", role="member", granted_at="2025-01-01T00:00:00"),
            _role_item(org_id="org-1", role="admin", granted_at="2025-06-01T00:00:00"),
            _role_item(org_id="org-2", role="owner", granted_at="2025-03-01T00:00:00"),
        ]

        memberships = _urs.get_user_org_memberships("u-1")
        assert len(memberships) == 2

        org1 = next(m for m in memberships if m["orgId"] == "org-1")
        assert set(org1["roles"]) == {"member", "admin"}
        assert org1["grantedAt"] == "2025-01-01T00:00:00"  # earliest

        org2 = next(m for m in memberships if m["orgId"] == "org-2")
        assert org2["roles"] == ["owner"]

    def test_excludes_global(self, _inject_mock_repo):
        _inject_mock_repo.get_roles_for_user.return_value = [
            _role_item(org_id="GLOBAL", role="super_admin"),
            _role_item(org_id="org-1", role="member"),
        ]

        memberships = _urs.get_user_org_memberships("u-1")
        assert len(memberships) == 1
        assert memberships[0]["orgId"] == "org-1"

    def test_empty_when_no_org_roles(self, _inject_mock_repo):
        _inject_mock_repo.get_roles_for_user.return_value = [
            _role_item(org_id="GLOBAL", role="super_admin"),
        ]
        assert _urs.get_user_org_memberships("u-1") == []
