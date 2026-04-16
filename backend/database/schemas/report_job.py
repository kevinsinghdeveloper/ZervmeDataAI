"""DynamoDB item schema for Report Job records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReportJobItem:
    org_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    report_id: str = ""
    status: str = "pending"  # pending | running | completed | failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Optional[str] = None  # JSON string
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "org_id": self.org_id, "id": self.id, "report_id": self.report_id,
            "status": self.status, "started_at": self.started_at,
            "completed_at": self.completed_at, "error_message": self.error_message,
            "result_data": self.result_data,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        import json
        rd = None
        if self.result_data:
            try:
                rd = json.loads(self.result_data)
            except (json.JSONDecodeError, TypeError):
                rd = self.result_data
        return {
            "orgId": self.org_id, "id": self.id, "reportId": self.report_id,
            "status": self.status, "startedAt": self.started_at,
            "completedAt": self.completed_at, "errorMessage": self.error_message,
            "resultData": rd,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "ReportJobItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
