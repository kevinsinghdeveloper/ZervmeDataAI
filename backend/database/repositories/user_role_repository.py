"""Unified UserRoleRepository — wraps any IRepository, backend-agnostic."""
from datetime import datetime, timezone
from typing import List, Optional
from abstractions.IRepository import IRepository
from abstractions.IUserRoleRepository import IUserRoleRepository
from database.schemas.user_role import UserRoleItem


class UserRoleRepository(IUserRoleRepository):

    def __init__(self, repo: IRepository):
        self._repo = repo

    def __getattr__(self, name):
        """Forward raw_* calls to the underlying repository."""
        return getattr(self._repo, name)

    # -- IRepository delegation --
    def get_by_id(self, id: str) -> Optional[dict]:
        return self._repo.get_by_id(id)

    def get_by_key(self, key: dict) -> Optional[dict]:
        return self._repo.get_by_key(key)

    def create(self, item: dict) -> dict:
        return self._repo.create(item)

    def upsert(self, item: dict) -> dict:
        return self._repo.upsert(item)

    def update(self, id: str, fields: dict) -> Optional[dict]:
        return self._repo.update(id, fields)

    def update_if(self, id: str, fields: dict, conditions: dict) -> bool:
        return self._repo.update_if(id, fields, conditions)

    def delete(self, id: str) -> bool:
        return self._repo.delete(id)

    def delete_by_key(self, key: dict) -> bool:
        return self._repo.delete_by_key(key)

    def delete_where(self, field: str, value) -> int:
        return self._repo.delete_where(field, value)

    def list_all(self, **filters) -> list:
        return self._repo.list_all(**filters)

    def find_by(self, field: str, value) -> list:
        return self._repo.find_by(field, value)

    def count(self, **filters) -> int:
        return self._repo.count(**filters)

    # -- UserRole-specific methods --
    def get_roles_for_user(self, user_id: str) -> List[UserRoleItem]:
        items = self._repo.find_by("user_id", str(user_id))
        return [UserRoleItem.from_item(i) for i in items if i.get("is_active", True)]

    def get_user_org_roles(self, user_id: str, org_id: str) -> List[UserRoleItem]:
        roles = self.get_roles_for_user(user_id)
        return [r for r in roles if r.org_id == org_id]

    def get_org_members(self, org_id: str) -> List[UserRoleItem]:
        items = self._repo.find_by("org_id", org_id)
        return [UserRoleItem.from_item(i) for i in items if i.get("is_active", True)]

    def get_org_member_ids(self, org_id: str) -> List[str]:
        members = self.get_org_members(org_id)
        return list(set(m.user_id for m in members))

    def is_super_admin(self, user_id: str) -> bool:
        item = self._repo.get_by_key({"user_id": user_id, "org_role": "GLOBAL#super_admin"})
        return bool(item and item.get("is_active", True))

    def grant_role(self, user_id: str, org_id: str, role: str,
                   granted_by: Optional[str] = None) -> UserRoleItem:
        if role == "super_admin":
            sk = UserRoleItem.make_global_role_sk(role)
            actual_org_id = "GLOBAL"
        else:
            sk = UserRoleItem.make_org_role_sk(org_id, role)
            actual_org_id = org_id

        now = datetime.now(timezone.utc).isoformat()
        item = UserRoleItem(
            user_id=user_id, org_role=sk, org_id=actual_org_id,
            role=role, granted_by=granted_by, granted_at=now,
            is_active=True, created_at=now, updated_at=now,
        )
        self._repo.upsert(item.to_item())
        return item

    def revoke_role(self, user_id: str, org_id: str, role: str) -> None:
        if role == "super_admin":
            sk = UserRoleItem.make_global_role_sk(role)
        else:
            sk = UserRoleItem.make_org_role_sk(org_id, role)
        now = datetime.now(timezone.utc).isoformat()
        item = self._repo.get_by_key({"user_id": user_id, "org_role": sk})
        if item:
            item["is_active"] = False
            item["updated_at"] = now
            self._repo.upsert(item)

    def revoke_all_org_roles(self, user_id: str, org_id: str) -> None:
        roles = self.get_user_org_roles(user_id, org_id)
        for r in roles:
            self.revoke_role(user_id, org_id, r.role)

    def is_last_owner(self, org_id: str) -> bool:
        members = self._repo.find_by("org_id", org_id)
        active_owners = [m for m in members
                         if m.get("role") == "owner" and m.get("is_active", True)]
        return len(active_owners) <= 1
