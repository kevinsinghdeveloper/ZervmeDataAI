"""
One-time migration: populate user_roles table from inline user fields.

Reads all existing users and creates corresponding entries in the user_roles table
based on their org_role and is_super_admin fields.

Usage:
    cd backend && python -m scripts.migrate_user_roles

    Or set env vars for remote DynamoDB:
    DYNAMODB_TABLE_PREFIX=zerve-dev AWS_REGION_NAME=us-east-1 python scripts/migrate_user_roles.py

This script is idempotent — running it multiple times won't create duplicates
because user_roles uses composite key (user_id, org_role).
"""
import os
import sys

# Add backend to path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import datetime
from database.dynamodb import get_table
from database.schemas.user import UserItem
from database.schemas.user_role import UserRoleItem


def migrate():
    users_table = get_table("users")
    roles_table = get_table("user_roles")

    # Scan all users
    items = []
    scan_kwargs = {}
    while True:
        resp = users_table.scan(**scan_kwargs)
        items.extend(resp.get("Items", []))
        if not resp.get("LastEvaluatedKey"):
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    print(f"Found {len(items)} users to process.")
    created_count = 0
    now = datetime.utcnow().isoformat()

    for item in items:
        user = UserItem.from_item(item)
        print(f"\nProcessing: {user.email} (id: {user.id})")

        # Migrate super_admin role
        if user.is_super_admin:
            role = UserRoleItem(
                user_id=user.id,
                org_role=UserRoleItem.make_global_role_sk("super_admin"),
                org_id="GLOBAL",
                role="super_admin",
                granted_by="migration",
                granted_at=user.created_at or now,
                is_active=True,
                created_at=user.created_at or now,
                updated_at=now,
            )
            roles_table.put_item(Item=role.to_item())
            print(f"  + super_admin (GLOBAL)")
            created_count += 1

        # Migrate org role
        if user.org_id and user.org_role:
            role = UserRoleItem(
                user_id=user.id,
                org_role=UserRoleItem.make_org_role_sk(user.org_id, user.org_role),
                org_id=user.org_id,
                role=user.org_role,
                granted_by="migration",
                granted_at=user.created_at or now,
                is_active=True,
                created_at=user.created_at or now,
                updated_at=now,
            )
            roles_table.put_item(Item=role.to_item())
            print(f"  + {user.org_role} in org {user.org_id}")
            created_count += 1

        if not user.is_super_admin and not (user.org_id and user.org_role):
            print(f"  (no roles to migrate)")

    print(f"\nMigration complete. Created {created_count} role entries for {len(items)} users.")


if __name__ == "__main__":
    migrate()
