"""DynamoDB item schema for Model Config records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfigItem:
    org_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    model_type_id: Optional[str] = None
    model_config: Optional[str] = None  # JSON string
    status: str = "active"  # active | inactive
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "org_id": self.org_id, "id": self.id, "name": self.name,
            "model_type_id": self.model_type_id, "model_config": self.model_config,
            "status": self.status,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        import json
        mc = None
        if self.model_config:
            try:
                mc = json.loads(self.model_config)
            except (json.JSONDecodeError, TypeError):
                mc = self.model_config
        return {
            "orgId": self.org_id, "id": self.id, "name": self.name,
            "modelTypeId": self.model_type_id, "modelConfig": mc,
            "status": self.status,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "ModelConfigItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
