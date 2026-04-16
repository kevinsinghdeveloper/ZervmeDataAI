"""DynamoDB item schema for OrgInvitation records."""
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OrgInvitationItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str = ""
    email: str = ""
    role: str = "member"  # owner | admin | manager | member
    token: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"  # pending | accepted | expired | revoked
    invited_by: str = ""
    expires_at: str = field(default_factory=lambda: (datetime.utcnow() + timedelta(days=7)).isoformat())
    expires_at_ttl: int = field(default_factory=lambda: int((datetime.utcnow() + timedelta(days=7)).timestamp()))
    accepted_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "id": self.id, "org_id": self.org_id, "email": self.email,
            "role": self.role, "token": self.token, "status": self.status,
            "invited_by": self.invited_by, "expires_at": self.expires_at,
            "expires_at_ttl": self.expires_at_ttl, "accepted_at": self.accepted_at,
            "created_at": self.created_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        return {
            "id": self.id, "orgId": self.org_id, "email": self.email,
            "role": self.role, "status": self.status,
            "invitedBy": self.invited_by, "expiresAt": self.expires_at,
            "acceptedAt": self.accepted_at, "createdAt": self.created_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "OrgInvitationItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
