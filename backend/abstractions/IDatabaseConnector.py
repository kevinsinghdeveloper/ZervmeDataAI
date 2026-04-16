"""Abstract base class for database connectors."""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class IDatabaseConnector(ABC):
    @abstractmethod
    def initialize(self, config: Optional[Dict] = None):
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

    @abstractmethod
    def close(self):
        pass
