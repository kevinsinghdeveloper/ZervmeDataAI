"""DynamoDB item schema for Report records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReportItem:
    org_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    project_id: Optional[str] = None
    report_type_id: Optional[str] = None
    model_id: Optional[str] = None
    dataset_config: Optional[str] = None  # JSON string
    report_config: Optional[str] = None  # JSON string
    status: str = "active"  # active | archived
    last_run_date: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "org_id": self.org_id, "id": self.id, "name": self.name,
            "project_id": self.project_id, "report_type_id": self.report_type_id,
            "model_id": self.model_id, "dataset_config": self.dataset_config,
            "report_config": self.report_config, "status": self.status,
            "last_run_date": self.last_run_date,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        import json
        dc = None
        if self.dataset_config:
            try:
                dc = json.loads(self.dataset_config)
            except (json.JSONDecodeError, TypeError):
                dc = self.dataset_config
        rc = None
        if self.report_config:
            try:
                rc = json.loads(self.report_config)
            except (json.JSONDecodeError, TypeError):
                rc = self.report_config
        return {
            "orgId": self.org_id, "id": self.id, "name": self.name,
            "projectId": self.project_id, "reportTypeId": self.report_type_id,
            "modelId": self.model_id, "datasetConfig": dc,
            "reportConfig": rc, "status": self.status,
            "lastRunDate": self.last_run_date,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "ReportItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
