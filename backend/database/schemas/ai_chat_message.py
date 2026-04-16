"""DynamoDB item schema for AI Chat Message records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AIChatMessageItem:
    session_id: str = ""
    timestamp_id: str = field(default_factory=lambda: f"{datetime.utcnow().isoformat()}#{uuid.uuid4()}")
    role: str = "user"  # user | assistant | system
    content: str = ""
    tool_calls: Optional[str] = None  # JSON
    chart_config: Optional[str] = None  # JSON for inline charts
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "session_id": self.session_id, "timestamp_id": self.timestamp_id,
            "role": self.role, "content": self.content,
            "tool_calls": self.tool_calls, "chart_config": self.chart_config,
            "created_at": self.created_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        import json
        chart = None
        if self.chart_config:
            try:
                chart = json.loads(self.chart_config)
            except (json.JSONDecodeError, TypeError):
                chart = self.chart_config
        return {
            "sessionId": self.session_id, "id": self.timestamp_id,
            "role": self.role, "content": self.content,
            "chartConfig": chart,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "AIChatMessageItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
