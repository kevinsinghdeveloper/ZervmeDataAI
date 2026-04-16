"""DynamoDB item schema for User records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    org_id: Optional[str] = None
    org_role: str = "member"  # owner | admin | manager | member
    is_super_admin: bool = False
    role: str = "member"  # Legacy compat - maps to org_role
    is_active: bool = True
    is_verified: bool = False
    status: str = "active"  # invited | active | deactivated
    timezone: str = "America/New_York"
    default_hourly_rate: Optional[str] = None  # Decimal as string
    weekly_capacity: int = 40  # hours per week
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    notification_preferences: Optional[str] = None  # JSON
    oauth_providers: Optional[str] = None  # JSON: {"google": {"provider_user_id": "...", "linked_at": "..."}}
    must_reset_password: bool = False
    invited_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        """Convert to DynamoDB item dict (removes None values)."""
        return {k: v for k, v in {
            "id": self.id, "email": self.email, "username": self.username,
            "first_name": self.first_name, "last_name": self.last_name,
            "org_id": self.org_id, "org_role": self.org_role,
            "is_super_admin": self.is_super_admin, "role": self.role,
            "is_active": self.is_active, "is_verified": self.is_verified,
            "status": self.status, "timezone": self.timezone,
            "default_hourly_rate": self.default_hourly_rate,
            "weekly_capacity": self.weekly_capacity,
            "avatar_url": self.avatar_url, "phone": self.phone,
            "notification_preferences": self.notification_preferences,
            "oauth_providers": self.oauth_providers,
            "must_reset_password": self.must_reset_password,
            "invited_at": self.invited_at,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        """Convert to API response format."""
        import json
        notif_prefs = None
        if self.notification_preferences:
            try:
                notif_prefs = json.loads(self.notification_preferences)
            except (json.JSONDecodeError, TypeError):
                notif_prefs = self.notification_preferences
        oauth = None
        if self.oauth_providers:
            try:
                oauth = json.loads(self.oauth_providers)
            except (json.JSONDecodeError, TypeError):
                oauth = self.oauth_providers
        return {
            "id": self.id, "email": self.email, "username": self.username,
            "firstName": self.first_name, "lastName": self.last_name,
            "orgId": self.org_id, "orgRole": self.org_role,
            "isSuperAdmin": self.is_super_admin, "role": self.role,
            "isActive": self.is_active, "isVerified": self.is_verified,
            "status": self.status, "timezone": self.timezone,
            "defaultHourlyRate": self.default_hourly_rate,
            "weeklyCapacity": self.weekly_capacity,
            "avatarUrl": self.avatar_url, "phone": self.phone,
            "notificationPreferences": notif_prefs,
            "oauthProviders": oauth,
            "mustResetPassword": self.must_reset_password,
            "invitedAt": self.invited_at,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "UserItem":
        """Create from DynamoDB item dict."""
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
