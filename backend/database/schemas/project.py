"""DynamoDB item schema for Project records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProjectItem:
    org_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    project_type: str = "ai_report"  # ai_report | research | analysis
    description: Optional[str] = None
    status: str = "active"  # active | archived | completed
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "org_id": self.org_id, "id": self.id, "name": self.name,
            "project_type": self.project_type, "description": self.description,
            "status": self.status,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "orgId": self.org_id, "id": self.id, "name": self.name,
            "projectType": self.project_type, "description": self.description,
            "status": self.status,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "ProjectItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
