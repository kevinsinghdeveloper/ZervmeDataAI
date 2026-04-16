"""DynamoDB item schema for UserRole records."""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserRoleItem:
    user_id: str = ""
    org_role: str = ""  # Composite SK: "{org_id}#{role}" or "GLOBAL#super_admin"
    org_id: str = ""  # Denormalized for GSI ("GLOBAL" for global roles)
    role: str = ""  # owner | admin | manager | member | super_admin
    granted_by: Optional[str] = None
    granted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @staticmethod
    def make_org_role_sk(org_id: str, role: str) -> str:
        """Build composite sort key for org-specific roles."""
        return f"{org_id}#{role}"

    @staticmethod
    def make_global_role_sk(role: str) -> str:
        """Build composite sort key for global roles."""
        return f"GLOBAL#{role}"

    def to_item(self) -> dict:
        """Convert to DynamoDB item dict (removes None values)."""
        return {k: v for k, v in {
            "user_id": self.user_id, "org_role": self.org_role,
            "org_id": self.org_id, "role": self.role,
            "granted_by": self.granted_by, "granted_at": self.granted_at,
            "is_active": self.is_active,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "userId": self.user_id, "orgId": self.org_id,
            "role": self.role, "grantedBy": self.granted_by,
            "grantedAt": self.granted_at, "isActive": self.is_active,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "UserRoleItem":
        """Create from DynamoDB item dict."""
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
