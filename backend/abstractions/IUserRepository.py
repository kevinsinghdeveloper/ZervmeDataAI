"""Specialized repository interface for users."""
from abc import abstractmethod
from typing import Optional
from abstractions.IRepository import IRepository


class IUserRepository(IRepository):

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[dict]:
        pass

    @abstractmethod
    def update_fields(self, user_id: str, fields: dict) -> bool:
        pass

    @abstractmethod
    def scan_count(self) -> int:
        """Count total users (for first-user detection)."""
        pass
