"""
Centralized user role query service for the user_roles table.

All backend components should use this module instead of reading
user.org_role or user.is_super_admin directly.

Call init_user_role_service(repo) at app startup to inject the repository.
"""
from datetime import datetime
from typing import List, Optional

from database.schemas.user_role import UserRoleItem

ORG_ROLE_HIERARCHY = ["member", "manager", "admin", "owner"]

# Module-level repository reference, set via init_user_role_service()
_repo = None


def init_user_role_service(user_role_repository) -> None:
    """Initialize the service with an IUserRoleRepository implementation."""
    global _repo
    _repo = user_role_repository


def _get_repo():
    """Get the repository. Raises if not initialized."""
    if _repo is None:
        raise RuntimeError("user_role_service not initialized. Call init_user_role_service() first.")
    return _repo


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_user_roles(user_id: str) -> List[UserRoleItem]:
    """Get all active roles for a user (across all orgs + global)."""
    return _get_repo().get_roles_for_user(user_id)


def get_user_org_roles(user_id: str, org_id: str) -> List[UserRoleItem]:
    """Get all active roles for a user within a specific org."""
    return _get_repo().get_user_org_roles(user_id, org_id)


def is_super_admin(user_id: str) -> bool:
    """Check if user has the global super_admin role."""
    return _get_repo().is_super_admin(user_id)


def get_user_highest_org_role(user_id: str, org_id: str) -> Optional[str]:
    """Get the highest role a user holds in a specific org."""
    roles = get_user_org_roles(user_id, org_id)
    if not roles:
        return None
    highest = None
    highest_level = -1
    for r in roles:
        if r.role in ORG_ROLE_HIERARCHY:
            level = ORG_ROLE_HIERARCHY.index(r.role)
            if level > highest_level:
                highest_level = level
                highest = r.role
    return highest


def user_meets_minimum_role(user_id: str, org_id: str, min_role: str) -> bool:
    """Check if user meets a minimum role threshold in an org."""
    highest = get_user_highest_org_role(user_id, org_id)
    if not highest:
        return False
    try:
        return ORG_ROLE_HIERARCHY.index(highest) >= ORG_ROLE_HIERARCHY.index(min_role)
    except ValueError:
        return False


def get_user_org_ids(user_id: str) -> List[str]:
    """Get all org IDs a user belongs to (excludes GLOBAL)."""
    roles = get_user_roles(user_id)
    return list(set(r.org_id for r in roles if r.org_id != "GLOBAL"))


def get_org_members(org_id: str) -> List[UserRoleItem]:
    """Get all active role entries for members of an org."""
    return _get_repo().get_org_members(org_id)


def get_org_member_ids(org_id: str) -> List[str]:
    """Get unique user IDs of active org members."""
    members = get_org_members(org_id)
    return list(set(m.user_id for m in members))


def grant_role(user_id: str, org_id: str, role: str,
               granted_by: Optional[str] = None) -> UserRoleItem:
    """Grant a role to a user in an org (or globally for super_admin)."""
    return _get_repo().grant_role(user_id, org_id, role, granted_by)


def revoke_role(user_id: str, org_id: str, role: str) -> None:
    """Revoke (soft-delete) a specific role."""
    return _get_repo().revoke_role(user_id, org_id, role)


def revoke_all_org_roles(user_id: str, org_id: str) -> None:
    """Revoke all roles a user has in a specific org."""
    return _get_repo().revoke_all_org_roles(user_id, org_id)


def is_last_owner(org_id: str) -> bool:
    """Check if there's only one active owner in the org."""
    return _get_repo().is_last_owner(org_id)


def get_user_org_memberships(user_id: str) -> List[dict]:
    """Get all org memberships for a user as API-friendly dicts."""
    all_roles = get_user_roles(user_id)
    org_map: dict = {}
    for r in all_roles:
        if r.org_id == "GLOBAL":
            continue
        if r.org_id not in org_map:
            org_map[r.org_id] = {"orgId": r.org_id, "roles": [], "grantedAt": r.granted_at}
        org_map[r.org_id]["roles"].append(r.role)
        if r.granted_at < org_map[r.org_id]["grantedAt"]:
            org_map[r.org_id]["grantedAt"] = r.granted_at
    return list(org_map.values())
