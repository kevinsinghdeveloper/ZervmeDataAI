"""DynamoDB item schema for AI Chat Session records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AIChatSessionItem:
    user_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str = ""
    title: str = "New Chat"
    message_count: int = 0
    last_message_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "user_id": self.user_id, "id": self.id, "org_id": self.org_id,
            "title": self.title, "message_count": self.message_count,
            "last_message_at": self.last_message_at,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "userId": self.user_id, "id": self.id, "orgId": self.org_id,
            "title": self.title, "messageCount": self.message_count,
            "lastMessageAt": self.last_message_at,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "AIChatSessionItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
