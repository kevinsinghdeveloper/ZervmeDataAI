from abc import abstractmethod
from typing import Dict, Optional


class IServiceManagerBase:
    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {}

    @abstractmethod
    def initialize(self):
        pass
