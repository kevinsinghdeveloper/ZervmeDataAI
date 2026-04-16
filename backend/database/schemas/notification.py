"""DynamoDB item schema for Notification records."""
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NotificationItem:
    user_id: str = ""
    timestamp_id: str = field(default_factory=lambda: f"{datetime.utcnow().isoformat()}#{uuid.uuid4()}")
    org_id: Optional[str] = None
    notification_type: str = "system"
    title: str = ""
    message: str = ""
    is_read: bool = False
    action_url: Optional[str] = None
    metadata: Optional[str] = None  # JSON
    expires_at_ttl: int = field(default_factory=lambda: int((datetime.utcnow() + timedelta(days=90)).timestamp()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "user_id": self.user_id, "timestamp_id": self.timestamp_id,
            "org_id": self.org_id, "notification_type": self.notification_type,
            "title": self.title, "message": self.message,
            "is_read": self.is_read, "action_url": self.action_url,
            "metadata": self.metadata, "expires_at_ttl": self.expires_at_ttl,
            "created_at": self.created_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "userId": self.user_id, "id": self.timestamp_id,
            "orgId": self.org_id, "type": self.notification_type,
            "title": self.title, "message": self.message,
            "isRead": self.is_read, "actionUrl": self.action_url,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "NotificationItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
