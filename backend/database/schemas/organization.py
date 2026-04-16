"""DynamoDB item schema for Organization records."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OrganizationItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    slug: str = ""
    owner_id: str = ""
    plan_tier: str = "free"  # free | starter | professional | enterprise
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[str] = None  # JSON: {timezone, weekStart, roundingIncrement, requireApproval, defaultBillableRate}
    member_count: int = 0
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_item(self) -> dict:
        return {k: v for k, v in {
            "id": self.id, "name": self.name, "slug": self.slug,
            "owner_id": self.owner_id, "plan_tier": self.plan_tier,
            "stripe_customer_id": self.stripe_customer_id,
            "stripe_subscription_id": self.stripe_subscription_id,
            "logo_url": self.logo_url, "settings": self.settings,
            "member_count": self.member_count, "is_active": self.is_active,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }.items() if v is not None}

    def to_api_dict(self) -> dict:
        import json
        settings = None
        if self.settings:
            try:
                settings = json.loads(self.settings)
            except (json.JSONDecodeError, TypeError):
                settings = self.settings
        return {
            "id": self.id, "name": self.name, "slug": self.slug,
            "ownerId": self.owner_id, "planTier": self.plan_tier,
            "stripeCustomerId": self.stripe_customer_id,
            "stripeSubscriptionId": self.stripe_subscription_id,
            "logoUrl": self.logo_url, "settings": settings,
            "memberCount": self.member_count, "isActive": self.is_active,
            "createdAt": self.created_at, "updatedAt": self.updated_at,
        }

    @classmethod
    def from_item(cls, item: dict) -> "OrganizationItem":
        return cls(**{k: v for k, v in item.items() if k in cls.__dataclass_fields__})
