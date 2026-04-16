# Database Abstraction Layer Refactor Plan

## Context

The backend is 100% coupled to DynamoDB — every manager imports `get_table()` and uses boto3's `Key`/`Attr` directly. There's no data access abstraction layer. This makes it impossible to swap databases without rewriting 50%+ of manager code.

This refactor introduces a **Repository Pattern** with pluggable database backends (DynamoDB, PostgreSQL), following the same approach used by `IStorageManager` → `S3StorageService` / `LocalStorageService`.

**Design decisions:**
- Generic base repository handles standard CRUD + common queries (covers ~70% of entities)
- Specialized repositories only for entities with complex access patterns (~5 entities)
- SQLAlchemy ORM for PostgreSQL backend
- `DB_TYPE` environment variable (defaults to `dynamodb`)
- Existing `@dataclass` schemas with `to_item()`/`from_item()`/`to_api_dict()` remain unchanged

---

## Architecture After Refactor

```
Controllers → Managers → Repositories (interfaces) → Implementations
                              │                        ├── DynamoDB (boto3)
                              │                        └── SQLAlchemy (PostgreSQL)
                              │
                         DatabaseService
                    (reads DB_TYPE, provides repos)
```

Managers will no longer import `get_table` or `boto3.dynamodb.conditions`. They access typed repositories via `self._db.users`, `self._db.time_entries`, `self._db.projects`, etc.

---

## Repository Design: Generic Base + Specialized Repos

### Generic Base (covers most entities)

One `IRepository[T]` interface with standard CRUD and common query patterns:

```python
class IRepository(ABC, Generic[T]):
    # Standard CRUD
    def get_by_id(self, id: str) -> T | None
    def create(self, item: T) -> T
    def update(self, id: str, fields: dict) -> T
    def delete(self, id: str) -> bool
    def list_all(self, **filters) -> list[T]

    # Common patterns (covers 80% of entity-specific methods)
    def find_by(self, field: str, value: str) -> list[T]
    def batch_get_by_ids(self, ids: list[str]) -> list[T]
```

One `DynamoDBRepository[T]` and one `SQLAlchemyRepository[T]` that implement this generically, configured with table/model metadata at construction:

```python
# Example — generic repo handles these entities with zero custom code:
db_service.clients = DynamoDBRepository(table="clients", schema=ClientItem)
db_service.projects = DynamoDBRepository(table="projects", schema=ProjectItem)
db_service.notifications = DynamoDBRepository(table="notifications", schema=NotificationItem)
```

### Entities using the generic repo (no custom code needed)

| Entity | Custom queries covered by `find_by()` |
|--------|---------------------------------------|
| `clients` | `find_by("org_id", ...)` |
| `projects` | `find_by("org_id", ...)`, `find_by("client_id", ...)` |
| `tasks` | `find_by("org_id", ...)`, `find_by("project_id", ...)` |
| `notifications` | `find_by("user_id", ...)` |
| `preset_narratives` | `find_by("org_id", ...)`, `find_by("user_id", ...)` |
| `integrations` | `find_by("org_id", ...)` |
| `subscription_plans` | Standard CRUD only |
| `ai_chat_sessions` | `find_by("user_id", ...)` |
| `ai_chat_messages` | `find_by("session_id", ...)` |
| `audit_logs` | `find_by("org_id", ...)` |
| `organizations` | `find_by("org_id", ...)` |
| `org_invitations` | `find_by("org_id", ...)`, `find_by("email", ...)` |

### Specialized repos (complex access patterns)

| Entity | Why it needs its own repo |
|--------|--------------------------|
| `TimeEntryRepository` | Running timer GSI, date range queries, batch create, calendar week/month queries |
| `UserRoleRepository` | Composite keys `{user_id}#{org_role}`, `begins_with` queries, `is_last_owner` logic |
| `TimesheetRepository` | Composite sort key `{user_id}#{week}`, status filtering across orgs |
| `ConfigRepository` | PK+SK compound key pattern, not a normal entity (settings, theme) |
| `UserRepository` | `find_by_email` (GSI), profile update with partial fields |

Each specialized repo extends the generic base and adds its custom methods.

---

## Phase 1: Abstractions & Generic Base (~4 files)

| File | Purpose |
|------|---------|
| `backend/abstractions/IDatabaseConnector.py` | `initialize(config)`, `health_check()`, `close()` |
| `backend/abstractions/IRepository.py` | Generic base: `get_by_id`, `create`, `update`, `delete`, `list_all`, `find_by`, `batch_get_by_ids` |
| `backend/database/repositories/interfaces/ITimeEntryRepository.py` | Extends `IRepository` — `find_by_user_date_range`, `find_running_timer`, `find_by_project_date`, `batch_create`, `count_by_project` |
| `backend/database/repositories/interfaces/IUserRoleRepository.py` | Extends `IRepository` — `get_roles_for_user`, `get_org_roles`, `grant_role`, `revoke_role`, `revoke_all_org_roles`, `get_org_members`, `get_org_member_ids`, `is_super_admin`, `is_last_owner` |
| `backend/database/repositories/interfaces/ITimesheetRepository.py` | Extends `IRepository` — `find_by_org_user_week`, `find_by_user_id`, `find_by_org_status` |
| `backend/database/repositories/interfaces/IConfigRepository.py` | `get_config(pk, sk)`, `put_config(pk, sk, data)`, `get_settings`, `put_settings` |
| `backend/database/repositories/interfaces/IUserRepository.py` | Extends `IRepository` — `find_by_email`, `update_fields` |

---

## Phase 2: DynamoDB Implementation (~7 files)

Create `backend/database/repositories/dynamodb/`:

| File | Purpose |
|------|---------|
| `connector.py` | `DynamoDBConnector(IDatabaseConnector)` — wraps existing `get_table()`, `TABLE_MAP`, boto3 resource logic from `database/dynamodb.py` |
| `base_repository.py` | `DynamoDBRepository(IRepository[T])` — generic impl handling standard CRUD, `find_by` (GSI/scan), `batch_get_by_ids`, scan pagination, reserved word escaping |
| `time_entry_repository.py` | Running timer GSI query, date range queries, batch create, calendar queries |
| `user_role_repository.py` | Composite key handling, `begins_with` queries, `is_last_owner` |
| `timesheet_repository.py` | Composite sort key queries, status filtering |
| `config_repository.py` | PK+SK compound key operations |
| `user_repository.py` | Email GSI lookup, partial field updates |

Key edge cases handled in DynamoDB repos:
- **Scan pagination**: `ExclusiveStartKey` loop encapsulated inside `list_all()` / `find_by()`
- **UpdateExpression building**: Moved from managers into repos
- **Reserved words**: `#s` for status, `#n` for name, `#r` for role
- **String booleans**: `is_running = "true"/"false"` for GSI compat
- **Batch operations**: `batch_get_item` (100 keys/call), `batch_writer` context manager

---

## Phase 3: DatabaseService (~2 files)

Create `backend/services/database/DatabaseService.py`:

- Extends `IServiceManagerBase` (existing pattern)
- Reads `DB_TYPE` env var — defaults to `dynamodb`, also accepts `postgres`
- `initialize()` creates the correct connector + all repository instances
  - Generic entities get `DynamoDBRepository(table=..., schema=...)` or `SQLAlchemyRepository(model=...)`
  - Specialized entities get their dedicated repo class
- Provides typed property accessors: `db_service.users`, `db_service.user_roles`, `db_service.time_entries`, etc.
- Injected into managers via existing `service_managers` dict as `"db"`

---

## Phase 4: Test Infrastructure Update

**Update `backend/tests/conftest.py` BEFORE touching managers:**
- Create `FakeDatabaseService` wrapping `FakeTable`-backed repositories
- Replace `patch("xxx.get_table")` calls with single `DatabaseService` patch
- Keep `FakeTable` class (proven to work, just wrap it)

**New test files** (per specialized repo + database service):
- `tests/test_time_entry_repository.py`
- `tests/test_user_role_repository.py`
- `tests/test_timesheet_repository.py`
- `tests/test_config_repository.py`
- `tests/test_user_repository.py`
- `tests/test_generic_repository.py` (covers all generic entities)
- `tests/test_database_service.py`

This ensures existing tests keep passing throughout manager refactoring.

---

## Phase 5: Refactor user_role_service.py

Current `backend/utils/user_role_service.py` directly calls `get_table("user_roles")`. Refactor to accept an injected `IUserRoleRepository`:

- Add `init_user_role_service(user_role_repository)` function called at startup
- All functions (`get_user_roles`, `is_super_admin`, `grant_role`, etc.) delegate to the injected repository
- `rbac_utils.py` stays as-is (calls user_role_service functions internally)
- **Must be called in `create_app()` before any route registration** to avoid import-time decorator issues

---

## Phase 6: Refactor Managers (one at a time)

Refactor in order of complexity (simplest first):

1. **AdminResourceManager** — ~3 DB calls
2. **BillingResourceManager** — ~5 DB calls
3. **NotificationResourceManager** — ~5 DB calls
4. **AuditResourceManager** — ~6 DB calls (mostly read-only)
5. **DashboardResourceManager** — ~8 DB calls (read-only aggregations)
6. **ConfigResourceManager** — ~10 DB calls
7. **ClientResourceManager** — ~7 DB calls
8. **TimesheetResourceManager** — ~8 DB calls
9. **SuperAdminResourceManager** — ~8 DB calls
10. **ProjectResourceManager** — ~12 DB calls (tasks, budget)
11. **AIChatResourceManager** — ~10 DB calls (sessions + messages)
12. **UserResourceManager** — ~15 DB calls (batch_get, profile updates)
13. **ReportResourceManager** — ~10 DB calls (complex aggregation)
14. **OrganizationResourceManager** — ~18 DB calls (invitations, members, batch_get)
15. **TimeEntryResourceManager** — ~20 DB calls (timer, calendar, narratives)
16. **AuthResourceManager** — ~22 DB calls (Cognito + DynamoDB, registration)

**For each manager:**
- Remove: `from database.dynamodb import get_table` and `from boto3.dynamodb.conditions import Key, Attr`
- Add: `self._db` property access (via `self._service_managers["db"]`)
- Replace all `get_table("x").operation(...)` calls with `self._db.x.method(...)` calls
- Keep schema dataclass usage unchanged (`TimeEntryItem.from_item()`, `.to_api_dict()`)
- Run `pytest tests/ -v` after each manager — all tests must pass before moving to next

**Before/after example** (timer query in TimeEntryResourceManager):
```python
# BEFORE:
table = get_table("time_entries")
resp = table.query(
    IndexName="RunningTimerIndex",
    KeyConditionExpression=Key("user_id").eq(str(user_id)) & Key("is_running").eq("true")
)
items = resp.get("Items", [])

# AFTER:
items = self._db.time_entries.find_running_timer(str(user_id))
```

---

## Phase 7: SQLAlchemy / PostgreSQL Implementation (~9 files)

**New dependencies** (add to `requirements.txt`):
- `SQLAlchemy>=2.0.0`, `alembic>=1.12.0`
- `psycopg2-binary>=2.9.0`

Create `backend/database/repositories/sqlalchemy/`:

| File | Purpose |
|------|---------|
| `connector.py` | `SQLAlchemyConnector(IDatabaseConnector)` — engine + session factory from `DATABASE_URL`, connection pooling |
| `models.py` | SQLAlchemy ORM models for all entities. Indexes mirror DynamoDB GSIs. Composite sort keys split into separate columns (repo handles mapping). |
| `base_repository.py` | `SQLAlchemyRepository(IRepository[T])` — generic impl with session queries |
| `time_entry_repository.py` | Date range queries, running timer, batch create |
| `user_role_repository.py` | Separate `org_id` + `role` columns (no composite string), proper JOINs |
| `timesheet_repository.py` | Separate `user_id` + `week_start` columns, status filtering |
| `config_repository.py` | PK+SK mapped to composite unique constraint |
| `user_repository.py` | Email unique index lookup, partial updates |

**Key SQL mappings:**

| DynamoDB Pattern | PostgreSQL Equivalent |
|------------------|----------------------|
| Composite PK+SK | `WHERE pk_col = ? AND sk_col = ?` |
| GSI query | `WHERE indexed_col = ?` (SQL index) |
| `begins_with(sk, prefix)` | Split into separate columns, query directly |
| `between(sk, a, b)` | `WHERE col BETWEEN ? AND ?` |
| `ScanIndexForward=False` | `ORDER BY col DESC` |
| `scan()` | `SELECT * FROM table` |
| `batch_get_item` | `WHERE pk IN (?, ?, ...)` |
| String boolean `"true"/"false"` | Native `BOOLEAN` (repo converts) |
| Composite sort keys `{org_id}#{role}` | Separate columns (proper relational design) |

---

## Phase 8: Migrations (Alembic)

Create `backend/alembic.ini` + `backend/alembic/`:

- `env.py` imports `Base` from SQLAlchemy connector
- Initial migration `001_initial_schema.py` creates all tables with indexes
- Only runs for PostgreSQL backend (DynamoDB tables stay managed by Terraform)
- `alembic upgrade head` added to deployment pipeline when `DB_TYPE=postgres`
- Alembic is the single source of truth for schema — no `create_all_tables()` even in dev

---

## Phase 9: Docker & Environment

**Update `docker-compose.yml`** with profiles:
- `dynamodb` profile: existing DynamoDB Local service
- `postgres` profile: PostgreSQL 16

**Update `.env.example`** with new variables:
- `DB_TYPE=dynamodb` (defaults to dynamodb)
- `DATABASE_URL=` (required when `DB_TYPE=postgres`)
- `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10`

**Update `backend/run_web_service.py`**:
- Replace `init_db()` call with `DatabaseService().initialize()`
- Add `db_service` to `service_managers` dict
- Call `init_user_role_service(db_service.user_roles)` before route registration

---

## Phase 10: Cleanup

- Remove `database/dynamodb.py` (logic now in `DynamoDBConnector`)
- Update `database/db.py` to delegate to `DatabaseService`
- Remove all dead `get_table` / `Key` / `Attr` imports from managers
- Update CI env vars to include `DB_TYPE=dynamodb`
- Update Lambda env vars in Terraform to include `DB_TYPE=dynamodb`

---

## Files Modified (existing)

| File | Change |
|------|--------|
| `backend/run_web_service.py` | Replace `init_db()` with `DatabaseService`, add to service_managers |
| `backend/utils/user_role_service.py` | Inject repository, remove `get_table` import |
| `backend/utils/rbac_utils.py` | Uses user_role_service (no direct DB access change needed) |
| `backend/abstractions/IResourceManager.py` | Add `_db` property shortcut |
| All 16 managers | Replace `get_table(...)` with `self._db.*` repos |
| `backend/database/db.py` | Delegate to DatabaseService |
| `backend/tests/conftest.py` | Replace FakeTable patches with FakeDatabaseService |
| `backend/requirements.txt` | Add SQLAlchemy, Alembic, psycopg2-binary |
| `docker-compose.yml` | Add postgres profile |
| `.env.example` | Add DB_TYPE, DATABASE_URL |
| `infrastructure/terraform/aws/backend.tf` | Add `DB_TYPE=dynamodb` to Lambda env |

## Files Created (new, ~22 files)

- 2 abstractions (`IDatabaseConnector.py`, `IRepository.py`)
- 5 specialized repository interfaces (`database/repositories/interfaces/`)
- 7 DynamoDB files (`database/repositories/dynamodb/` — connector + generic base + 5 specialized)
- 9 SQLAlchemy files (`database/repositories/sqlalchemy/` — connector + models + generic base + 5 specialized + 1 alembic migration)
- 2 DatabaseService files (`services/database/`)
- 7 test files (generic repo + 5 specialized + database service)
- 2 Alembic config files (`alembic.ini`, `alembic/env.py`)

---

## Verification Plan

1. After Phase 2, run DynamoDB repository unit tests
2. After Phase 4, run `pytest tests/ -v` — all existing tests must pass with FakeDatabaseService
3. After each manager in Phase 6, run `pytest tests/ -v` — must pass before next manager
4. After Phase 7, spin up PostgreSQL via docker-compose and run integration tests
5. After Phase 9, run full test suite against both DynamoDB and PostgreSQL
6. Final: deploy to Lambda with `DB_TYPE=dynamodb` and verify production behavior unchanged
