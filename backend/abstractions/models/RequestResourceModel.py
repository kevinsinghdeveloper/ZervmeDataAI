from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class RequestResourceModel:
    def __init__(self, data: Optional[Dict[str, Any]] = None, user_id: Optional[UUID] = None):
        self.data = data or {}
        self.user_id = user_id
