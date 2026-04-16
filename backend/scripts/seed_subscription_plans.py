"""
Seed subscription plans into DynamoDB.

Usage:
    # From the backend directory with AWS credentials configured:
    python -m scripts.seed_subscription_plans

    # Or with custom table prefix:
    DYNAMODB_TABLE_PREFIX=zerve-dev python -m scripts.seed_subscription_plans

    # For local DynamoDB:
    DYNAMODB_ENDPOINT_URL=http://localhost:8000 python -m scripts.seed_subscription_plans
"""
import json
import sys
import os
import uuid
from datetime import datetime

# Add backend root to path so we can import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.database.DatabaseService import DatabaseService
from database.schemas.subscription_plan import SubscriptionPlanItem


PLANS = [
    SubscriptionPlanItem(
        id=str(uuid.uuid4()),
        name="Free",
        tier="free",
        stripe_price_id="",
        price_monthly=0.0,
        price_yearly=0.0,
        max_members=1,
        max_projects=2,
        features=json.dumps([
            "1 team member",
            "2 projects",
            "Basic time tracking",
            "Manual time entries",
            "Personal dashboard",
        ]),
        is_active=True,
    ),
    SubscriptionPlanItem(
        id=str(uuid.uuid4()),
        name="Starter",
        tier="starter",
        stripe_price_id="",
        price_monthly=12.0,
        price_yearly=115.0,  # ~20% annual discount
        max_members=5,
        max_projects=10,
        features=json.dumps([
            "Up to 5 team members",
            "10 projects",
            "Timer & manual tracking",
            "Weekly timesheets",
            "Basic reports",
            "Client management",
            "Email support",
        ]),
        is_active=True,
    ),
    SubscriptionPlanItem(
        id=str(uuid.uuid4()),
        name="Professional",
        tier="professional",
        stripe_price_id="",
        price_monthly=29.0,
        price_yearly=278.0,  # ~20% annual discount
        max_members=0,  # 0 = unlimited
        max_projects=0,
        features=json.dumps([
            "Unlimited team members",
            "Unlimited projects",
            "Timer & manual tracking",
            "Weekly timesheets with approval",
            "Advanced reports & analytics",
            "Client management",
            "Budget tracking",
            "AI time assistant",
            "Narrative presets",
            "Export to CSV/PDF",
            "Priority email support",
        ]),
        is_active=True,
    ),
    SubscriptionPlanItem(
        id=str(uuid.uuid4()),
        name="Enterprise",
        tier="enterprise",
        stripe_price_id="",
        price_monthly=79.0,
        price_yearly=758.0,  # ~20% annual discount
        max_members=0,
        max_projects=0,
        features=json.dumps([
            "Everything in Professional",
            "Unlimited everything",
            "Custom integrations",
            "SSO / SAML authentication",
            "Advanced security controls",
            "Dedicated account manager",
            "Custom onboarding",
            "SLA guarantee",
            "Priority support",
            "API access",
        ]),
        is_active=True,
    ),
]


def seed_plans() -> None:
    db = DatabaseService()
    db.initialize()
    now = datetime.utcnow().isoformat()

    # Check for existing plans
    existing = db.subscription_plans.list_all()
    if existing:
        print(f"Found {len(existing)} existing plans.")
        confirm = input("Delete existing plans and re-seed? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted. No changes made.")
            return
        for item in existing:
            item_id = item.id if hasattr(item, "id") else item.get("id")
            db.subscription_plans.delete(item_id)
            name = item.name if hasattr(item, "name") else item.get("name", item_id)
            print(f"  Deleted: {name}")

    for plan in PLANS:
        plan.created_at = now
        plan.updated_at = now
        db.subscription_plans.create(plan)
        print(f"  Created: {plan.name} ({plan.tier}) - ${plan.price_monthly}/mo, ${plan.price_yearly}/yr")

    print(f"\nSeeded {len(PLANS)} subscription plans successfully.")


if __name__ == "__main__":
    seed_plans()
