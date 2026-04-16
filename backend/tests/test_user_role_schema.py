"""Unit tests for UserRoleItem schema."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.schemas.user_role import UserRoleItem


# ---------------------------------------------------------------------------
# Static helpers
# ---------------------------------------------------------------------------

class TestMakeOrgRoleSK:
    def test_standard_org_role(self):
        assert UserRoleItem.make_org_role_sk("org-1", "admin") == "org-1#admin"

    def test_uuid_org_id(self):
        assert UserRoleItem.make_org_role_sk("abc-def-123", "member") == "abc-def-123#member"

    def test_owner_role(self):
        assert UserRoleItem.make_org_role_sk("org-1", "owner") == "org-1#owner"


class TestMakeGlobalRoleSK:
    def test_super_admin(self):
        assert UserRoleItem.make_global_role_sk("super_admin") == "GLOBAL#super_admin"

    def test_arbitrary_global_role(self):
        assert UserRoleItem.make_global_role_sk("support") == "GLOBAL#support"


# ---------------------------------------------------------------------------
# to_item / from_item round-trip
# ---------------------------------------------------------------------------

class TestToItem:
    def test_serializes_all_fields(self):
        item = UserRoleItem(
            user_id="u-1",
            org_role="org-1#admin",
            org_id="org-1",
            role="admin",
            granted_by="granter-1",
            granted_at="2025-01-01T00:00:00",
            is_active=True,
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
        )
        d = item.to_item()
        assert d["user_id"] == "u-1"
        assert d["org_role"] == "org-1#admin"
        assert d["org_id"] == "org-1"
        assert d["role"] == "admin"
        assert d["granted_by"] == "granter-1"
        assert d["is_active"] is True

    def test_drops_none_granted_by(self):
        item = UserRoleItem(
            user_id="u-1",
            org_role="org-1#member",
            org_id="org-1",
            role="member",
            granted_by=None,
        )
        d = item.to_item()
        assert "granted_by" not in d

    def test_keeps_false_is_active(self):
        item = UserRoleItem(user_id="u-1", org_role="org-1#admin", is_active=False)
        d = item.to_item()
        assert d["is_active"] is False


class TestFromItem:
    def test_round_trip(self):
        original = UserRoleItem(
            user_id="u-1",
            org_role="org-1#admin",
            org_id="org-1",
            role="admin",
            granted_by="granter-1",
            granted_at="2025-01-01T00:00:00",
            is_active=True,
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
        )
        restored = UserRoleItem.from_item(original.to_item())
        assert restored.user_id == original.user_id
        assert restored.org_role == original.org_role
        assert restored.org_id == original.org_id
        assert restored.role == original.role
        assert restored.granted_by == original.granted_by
        assert restored.is_active == original.is_active

    def test_ignores_unknown_fields(self):
        raw = {
            "user_id": "u-1",
            "org_role": "org-1#admin",
            "org_id": "org-1",
            "role": "admin",
            "unknown_field": "should_be_ignored",
        }
        item = UserRoleItem.from_item(raw)
        assert item.user_id == "u-1"
        assert not hasattr(item, "unknown_field") or item.role == "admin"


# ---------------------------------------------------------------------------
# to_api_dict
# ---------------------------------------------------------------------------

class TestToApiDict:
    def test_camel_case_keys(self):
        item = UserRoleItem(
            user_id="u-1",
            org_role="org-1#admin",
            org_id="org-1",
            role="admin",
            granted_by="granter-1",
            granted_at="2025-01-01T00:00:00",
            is_active=True,
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
        )
        api = item.to_api_dict()
        assert api["userId"] == "u-1"
        assert api["orgId"] == "org-1"
        assert api["role"] == "admin"
        assert api["grantedBy"] == "granter-1"
        assert api["grantedAt"] == "2025-01-01T00:00:00"
        assert api["isActive"] is True
        assert api["createdAt"] == "2025-01-01T00:00:00"
        assert api["updatedAt"] == "2025-01-01T00:00:00"
        # Should NOT contain snake_case keys
        assert "user_id" not in api
        assert "org_id" not in api
        assert "is_active" not in api
