"""Specialized repository interface for config (PK+SK compound key pattern)."""
from abc import ABC, abstractmethod
from typing import Optional


class IConfigRepository(ABC):

    @abstractmethod
    def get_config(self, pk: str, sk: str) -> Optional[dict]:
        pass

    @abstractmethod
    def put_config(self, pk: str, sk: str, data: dict) -> dict:
        pass

    @abstractmethod
    def get_settings(self) -> Optional[dict]:
        pass

    @abstractmethod
    def put_settings(self, data: dict) -> dict:
        pass

    @abstractmethod
    def scan_by_pk(self, pk: str) -> list:
        pass
