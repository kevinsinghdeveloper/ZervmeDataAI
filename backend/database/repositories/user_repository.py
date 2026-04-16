"""Unified UserRepository — wraps any IRepository, backend-agnostic."""
from datetime import datetime, timezone
from typing import Optional
from abstractions.IRepository import IRepository
from abstractions.IUserRepository import IUserRepository


class UserRepository(IUserRepository):

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

    # -- User-specific methods --
    def find_by_email(self, email: str) -> Optional[dict]:
        results = self._repo.find_by("email", email)
        return results[0] if results else None

    def update_fields(self, user_id: str, fields: dict) -> bool:
        fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = self._repo.update(user_id, fields)
        return result is not None

    def scan_count(self) -> int:
        return self._repo.count()
