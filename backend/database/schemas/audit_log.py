"""DynamoDB item schema for AuditLog records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class AuditLogItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    org_id: Optional[str] = None
    action: str = ""
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None  # JSON string
    ip_address: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "id": self.id, "user_id": self.user_id, "org_id": self.org_id,
            "action": self.action, "resource": self.resource,
            "resource_id": self.resource_id, "details": self.details,
            "ip_address": self.ip_address, "timestamp": self.timestamp,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        details = None
        if self.details:
            try:
                details = json.loads(self.details)
            except (json.JSONDecodeError, TypeError):
                details = self.details
        return {
            "id": self.id, "userId": self.user_id, "orgId": self.org_id,
            "action": self.action, "resource": self.resource,
            "resourceId": self.resource_id, "details": details,
            "ipAddress": self.ip_address, "timestamp": self.timestamp,
        }

    @classmethod
    def from_item(cls, item: dict) -> "AuditLogItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
