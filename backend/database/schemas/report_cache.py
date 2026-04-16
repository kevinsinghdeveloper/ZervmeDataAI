"""DynamoDB item schema for Report Cache records."""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReportCacheItem:
    report_id: str = ""
    cache_key: str = ""
    cache_data: Optional[str] = None  # JSON string
    expires_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "report_id": self.report_id, "cache_key": self.cache_key,
            "cache_data": self.cache_data, "expires_at": self.expires_at,
            "created_at": self.created_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        import json
        cd = None
        if self.cache_data:
            try:
                cd = json.loads(self.cache_data)
            except (json.JSONDecodeError, TypeError):
                cd = self.cache_data
        return {
            "reportId": self.report_id, "cacheKey": self.cache_key,
            "cacheData": cd, "expiresAt": self.expires_at,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "ReportCacheItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
