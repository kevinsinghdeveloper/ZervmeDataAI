"""DynamoDB item schema for Dataset records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DatasetItem:
    org_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    domain_data: Optional[str] = None  # JSON string
    data_source: Optional[str] = None
    status: str = "active"  # active | archived
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "org_id": self.org_id, "id": self.id, "name": self.name,
            "description": self.description, "domain_data": self.domain_data,
            "data_source": self.data_source, "status": self.status,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        import json
        dd = None
        if self.domain_data:
            try:
                dd = json.loads(self.domain_data)
            except (json.JSONDecodeError, TypeError):
                dd = self.domain_data
        return {
            "orgId": self.org_id, "id": self.id, "name": self.name,
            "description": self.description, "domainData": dd,
            "dataSource": self.data_source, "status": self.status,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "DatasetItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
