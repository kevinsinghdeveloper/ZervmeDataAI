"""Generic repository interface for all entities."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


class IRepository(ABC, Generic[T]):

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def get_by_key(self, key: dict) -> Optional[dict]:
        """Get item by arbitrary key fields (supports composite keys)."""
        pass

    @abstractmethod
    def create(self, item: dict) -> dict:
        pass

    @abstractmethod
    def upsert(self, item: dict) -> dict:
        """Create or replace item (DynamoDB put_item semantics)."""
        pass

    @abstractmethod
    def update(self, id: str, fields: dict) -> Optional[dict]:
        pass

    @abstractmethod
    def update_if(self, id: str, fields: dict, conditions: dict) -> bool:
        """Update only if conditions match. Returns True if updated."""
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        pass

    @abstractmethod
    def delete_by_key(self, key: dict) -> bool:
        """Delete by arbitrary key fields (supports composite keys)."""
        pass

    @abstractmethod
    def delete_where(self, field: str, value) -> int:
        """Delete all items where field == value. Returns count deleted."""
        pass

    @abstractmethod
    def list_all(self, **filters) -> list:
        pass

    @abstractmethod
    def find_by(self, field: str, value) -> list:
        pass

    @abstractmethod
    def count(self, **filters) -> int:
        """Count items, optionally filtered."""
        pass
