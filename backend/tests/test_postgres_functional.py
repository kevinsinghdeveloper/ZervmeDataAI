"""Functional tests for PostgreSQL backend.

Runs real CRUD operations against a PostgreSQL database to verify
the repository layer works correctly with a real database.

Requires: docker-compose.test.yml running (postgres on port 5433)
Set DATABASE_URL=postgresql://zerve:zerve@localhost:5433/zerve_test

Skip with: pytest -m "not postgres"
"""
import os
import uuid
import pytest
from datetime import datetime, timezone

# Skip all tests in this module if no test postgres available
pytestmark = pytest.mark.postgres

TEST_DB_URL = os.getenv("DATABASE_URL", "postgresql://zerve:zerve@localhost:5433/zerve_test")


def _can_connect():
    """Check if test postgres is available."""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(TEST_DB_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


skip_no_postgres = pytest.mark.skipif(
    not _can_connect(),
    reason="Test PostgreSQL not available (start with docker-compose.test.yml)"
)


@pytest.fixture(scope="module")
def db_service():
    """Create a DatabaseService configured for PostgreSQL."""
    os.environ["DB_TYPE"] = "postgres"
    os.environ["DATABASE_URL"] = TEST_DB_URL

    from services.database.DatabaseService import DatabaseService
    svc = DatabaseService()
    svc.initialize()
    yield svc

    # Cleanup: drop all data
    from database.repositories.connectors.SQLAlchemyConnector import Base
    engine = svc.users._repo._connector.engine
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Restore env
    os.environ["DB_TYPE"] = "dynamodb"


# ===========================================================================
# USER REPOSITORY
# ===========================================================================

@skip_no_postgres
class TestPostgresUserRepository:

    def test_create_and_get_by_id(self, db_service):
        from database.schemas.user import UserItem
        user = UserItem(
            id=str(uuid.uuid4()),
            email=f"test-{uuid.uuid4().hex[:8]}@example.com",
            first_name="Test",
            last_name="User",
            org_id="org-test",
            is_active=True,
        )
        db_service.users.create(user.to_item())
        fetched = db_service.users.get_by_id(user.id)

        assert fetched is not None
        assert fetched["id"] == user.id
        assert fetched["email"] == user.email
        assert fetched["first_name"] == "Test"

    def test_find_by_email(self, db_service):
        from database.schemas.user import UserItem
        email = f"findme-{uuid.uuid4().hex[:8]}@example.com"
        user = UserItem(id=str(uuid.uuid4()), email=email, first_name="Find")
        db_service.users.create(user.to_item())

        found = db_service.users.find_by_email(email)
        assert found is not None
        assert found["email"] == email

    def test_find_by_email_not_found(self, db_service):
        found = db_service.users.find_by_email("nonexistent@example.com")
        assert found is None

    def test_update_fields(self, db_service):
        from database.schemas.user import UserItem
        user = UserItem(id=str(uuid.uuid4()), email=f"upd-{uuid.uuid4().hex[:8]}@example.com")
        db_service.users.create(user.to_item())

        db_service.users.update_fields(user.id, {"first_name": "Updated"})
        fetched = db_service.users.get_by_id(user.id)
        assert fetched["first_name"] == "Updated"

    def test_delete(self, db_service):
        from database.schemas.user import UserItem
        user = UserItem(id=str(uuid.uuid4()), email=f"del-{uuid.uuid4().hex[:8]}@example.com")
        db_service.users.create(user.to_item())

        db_service.users.delete(user.id)
        fetched = db_service.users.get_by_id(user.id)
        assert fetched is None

    def test_scan_count(self, db_service):
        count = db_service.users.scan_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_get_by_key(self, db_service):
        from database.schemas.user import UserItem
        user = UserItem(id=str(uuid.uuid4()), email=f"key-{uuid.uuid4().hex[:8]}@example.com")
        db_service.users.create(user.to_item())

        item = db_service.users.get_by_key({"id": user.id})
        assert item is not None
        assert item["id"] == user.id


# ===========================================================================
# USER ROLE REPOSITORY
# ===========================================================================

@skip_no_postgres
class TestPostgresUserRoleRepository:

    def test_grant_and_get_roles(self, db_service):
        user_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())

        db_service.user_roles.grant_role(user_id, org_id, "member", "system")
        roles = db_service.user_roles.get_roles_for_user(user_id)

        assert len(roles) == 1
        assert roles[0].role == "member"
        assert roles[0].org_id == org_id

    def test_grant_super_admin(self, db_service):
        user_id = str(uuid.uuid4())
        db_service.user_roles.grant_role(user_id, "GLOBAL", "super_admin", "system")

        assert db_service.user_roles.is_super_admin(user_id) is True

    def test_is_not_super_admin(self, db_service):
        assert db_service.user_roles.is_super_admin("nonexistent") is False

    def test_get_user_org_roles(self, db_service):
        user_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())

        db_service.user_roles.grant_role(user_id, org_id, "member", "system")
        db_service.user_roles.grant_role(user_id, org_id, "admin", "system")

        roles = db_service.user_roles.get_user_org_roles(user_id, org_id)
        assert len(roles) == 2
        role_names = {r.role for r in roles}
        assert role_names == {"member", "admin"}

    def test_revoke_role(self, db_service):
        user_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())

        db_service.user_roles.grant_role(user_id, org_id, "member", "system")
        db_service.user_roles.revoke_role(user_id, org_id, "member")

        roles = db_service.user_roles.get_user_org_roles(user_id, org_id)
        assert len(roles) == 0  # is_active=False filtered out

    def test_get_org_members(self, db_service):
        org_id = str(uuid.uuid4())
        u1 = str(uuid.uuid4())
        u2 = str(uuid.uuid4())

        db_service.user_roles.grant_role(u1, org_id, "member", "system")
        db_service.user_roles.grant_role(u2, org_id, "admin", "system")

        members = db_service.user_roles.get_org_members(org_id)
        assert len(members) == 2

    def test_is_last_owner(self, db_service):
        org_id = str(uuid.uuid4())
        u1 = str(uuid.uuid4())

        db_service.user_roles.grant_role(u1, org_id, "owner", "system")
        assert db_service.user_roles.is_last_owner(org_id) is True

        u2 = str(uuid.uuid4())
        db_service.user_roles.grant_role(u2, org_id, "owner", "system")
        assert db_service.user_roles.is_last_owner(org_id) is False


# ===========================================================================
# TIME ENTRY REPOSITORY
# ===========================================================================

@skip_no_postgres
class TestPostgresTimeEntryRepository:

    def test_create_and_get(self, db_service):
        from database.schemas.time_entry import TimeEntryItem
        entry = TimeEntryItem(
            org_id="org-test",
            user_id="user-test",
            project_id="proj-1",
            date="2024-01-15",
            description="Test entry",
            duration_minutes=120,
            is_billable=True,
        )
        db_service.time_entries.create(entry.to_item())

        fetched = db_service.time_entries.get_by_key({"id": entry.id})
        assert fetched is not None
        assert fetched["description"] == "Test entry"
        assert fetched["duration_minutes"] == 120

    def test_find_by_user_date_range(self, db_service):
        from database.schemas.time_entry import TimeEntryItem

        user_id = f"user-{uuid.uuid4().hex[:8]}"
        for i, date in enumerate(["2024-01-15", "2024-01-16", "2024-01-17"]):
            entry = TimeEntryItem(
                org_id="org-test", user_id=user_id,
                date=date, description=f"Entry {i}",
                duration_minutes=60 * (i + 1),
            )
            db_service.time_entries.create(entry.to_item())

        results = db_service.time_entries.find_by_user_date_range(
            user_id, "2024-01-15", "2024-01-16"
        )
        assert len(results) == 2
        assert all(r.user_id == user_id for r in results)

    def test_find_running_timer(self, db_service):
        from database.schemas.time_entry import TimeEntryItem

        user_id = f"user-timer-{uuid.uuid4().hex[:8]}"
        entry = TimeEntryItem(
            org_id="org-test", user_id=user_id,
            date="2024-01-15", is_running="true",
            timer_started_at=datetime.now(timezone.utc).isoformat(),
            source="timer",
        )
        db_service.time_entries.create(entry.to_item())

        results = db_service.time_entries.find_running_timer(user_id)
        assert len(results) == 1
        assert results[0]["is_running"] == "true"

    def test_batch_create(self, db_service):
        from database.schemas.time_entry import TimeEntryItem

        org_id = f"org-bc-{uuid.uuid4().hex[:8]}"
        entries = []
        for i in range(5):
            entries.append(TimeEntryItem(
                org_id=org_id, user_id="user-bc",
                date="2024-02-01", description=f"Batch {i}",
                duration_minutes=30,
            ))

        count = db_service.time_entries.batch_create(entries)
        assert count == 5

    def test_update_and_delete(self, db_service):
        from database.schemas.time_entry import TimeEntryItem
        entry = TimeEntryItem(
            org_id="org-test", user_id="user-ud",
            date="2024-01-20", description="To update",
            duration_minutes=30,
        )
        db_service.time_entries.create(entry.to_item())

        db_service.time_entries.update(entry.id, {"description": "Updated", "duration_minutes": 90})
        fetched = db_service.time_entries.get_by_key({"id": entry.id})
        assert fetched["description"] == "Updated"

        db_service.time_entries.delete(entry.id)
        fetched = db_service.time_entries.get_by_key({"id": entry.id})
        assert fetched is None


# ===========================================================================
# ORGANIZATION + GENERIC REPO
# ===========================================================================

@skip_no_postgres
class TestPostgresOrganizationRepository:

    def test_create_and_get(self, db_service):
        from database.schemas.organization import OrganizationItem
        org = OrganizationItem(
            name="Test Org", slug="test-org",
            owner_id="user-1", member_count=1,
        )
        db_service.organizations.create(org.to_item())

        fetched = db_service.organizations.get_by_id(org.id)
        assert fetched is not None
        assert fetched["name"] == "Test Org"
        assert fetched["slug"] == "test-org"

    def test_get_by_key(self, db_service):
        from database.schemas.organization import OrganizationItem
        org = OrganizationItem(name="Key Org", slug="key-org", owner_id="user-1")
        db_service.organizations.create(org.to_item())

        item = db_service.organizations.get_by_key({"id": org.id})
        assert item is not None
        assert item["name"] == "Key Org"

    def test_update(self, db_service):
        from database.schemas.organization import OrganizationItem
        org = OrganizationItem(name="Before", slug="before", owner_id="user-1")
        db_service.organizations.create(org.to_item())

        db_service.organizations.update(org.id, {"name": "After"})
        fetched = db_service.organizations.get_by_id(org.id)
        assert fetched["name"] == "After"


# ===========================================================================
# CONFIG REPOSITORY
# ===========================================================================

@skip_no_postgres
class TestPostgresConfigRepository:

    def test_put_and_get_settings(self, db_service):
        settings = {"theme": "dark", "language": "en"}
        db_service.config.put_settings(settings)

        fetched = db_service.config.get_settings()
        assert fetched is not None
        assert fetched["theme"] == "dark"
        assert fetched["language"] == "en"

    def test_put_and_get_config(self, db_service):
        db_service.config.put_config("FEATURE", "flags", {"beta": True})

        fetched = db_service.config.get_config("FEATURE", "flags")
        assert fetched is not None
        assert fetched["beta"] is True

    def test_scan_by_pk(self, db_service):
        db_service.config.put_config("THEME", "light", {"primary": "#fff"})
        db_service.config.put_config("THEME", "dark", {"primary": "#000"})

        results = db_service.config.scan_by_pk("THEME")
        assert len(results) >= 2


# ===========================================================================
# TIMESHEET REPOSITORY
# ===========================================================================

@skip_no_postgres
class TestPostgresTimesheetRepository:

    def test_create_and_find(self, db_service):
        from database.schemas.timesheet import TimesheetItem
        org_id = f"org-ts-{uuid.uuid4().hex[:8]}"
        user_id = "user-ts"
        week_start = "2024-01-15"
        user_week = f"{user_id}#{week_start}"

        ts = TimesheetItem(
            org_id=org_id, user_week=user_week,
            user_id=user_id, week_start=week_start,
            status="draft", total_hours=40.0, billable_hours=32.0,
        )
        db_service.timesheets.create(ts.to_item())

        fetched = db_service.timesheets.find_by_org_user_week(org_id, user_id, week_start)
        assert fetched is not None
        assert fetched.status == "draft"
        assert fetched.total_hours == 40.0

    def test_find_by_org_status(self, db_service):
        from database.schemas.timesheet import TimesheetItem
        org_id = f"org-ts2-{uuid.uuid4().hex[:8]}"

        for i, status in enumerate(["submitted", "submitted", "approved"]):
            ts = TimesheetItem(
                org_id=org_id, user_week=f"user-{i}#2024-01-15",
                user_id=f"user-{i}", week_start="2024-01-15",
                status=status,
            )
            db_service.timesheets.create(ts.to_item())

        submitted = db_service.timesheets.find_by_org_status(org_id, "submitted")
        assert len(submitted) == 2
