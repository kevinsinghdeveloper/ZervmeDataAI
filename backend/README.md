# Backend -- Flask API on AWS Lambda

The backend is a Flask application running on AWS Lambda via [apig-wsgi](https://github.com/adamchainz/apig-wsgi). It provides REST API endpoints for the Zerve My Time time tracking application.

## Local Development

### Prerequisites

- Python 3.10+
- AWS credentials (IAM user `zerve-local-dev` or SSO session)
- Docker (optional, for PostgreSQL functional tests)

### Setup

```bash
cd backend

# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt
pip install boto3                # Lambda provides this, but local dev needs it

# 3. Create .env (see .env section below)

# 4. Run the server
python run_web_service.py        # http://localhost:8000 (debug=true)
```

### Verify it works

```bash
curl http://localhost:8000/api/health
# {"service":"zerve-mytime-backend","status":"healthy","version":"2.0.0"}
```

### Debug with breakpoints

1. Set your IDE's Python interpreter to `backend/.venv/bin/python`
2. Create a run/debug configuration for `run_web_service.py`
3. Set breakpoints in any controller, manager, or service
4. Flask restarts automatically on file changes (debug mode)

### .env file

Create `backend/.env` with these values (the file is gitignored):

```bash
# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
FLASK_DEBUG=true
FLASK_SECRET_KEY=local-dev-secret-key
CORS_ORIGINS=http://localhost:3000

# Database -- set DB_TYPE to switch backends
DB_TYPE=dynamodb                 # "dynamodb" (default) or "postgres"
DATABASE_URL=postgresql://zerve:zerve@localhost:5432/zerve  # Only needed when DB_TYPE=postgres

# AWS (required for DynamoDB backend)
AWS_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>

# DynamoDB
DYNAMODB_TABLE_PREFIX=zerve-dev

# Cognito
COGNITO_USER_POOL_ID=us-east-1_R7LaDuCWI
COGNITO_CLIENT_ID=1259agca7ctc1fbuglifa6tr1i

# S3 Uploads
UPLOADS_BUCKET=zerve-dev-uploads-396326422827

# Optional
STRIPE_SECRET_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

### Running tests

```bash
source .venv/bin/activate

# Unit tests (no external dependencies)
pytest tests/ -m "not postgres" -v   # 269 tests

# PostgreSQL functional tests (requires Docker)
sudo docker compose -f ../docker-compose.test.yml up -d
DATABASE_URL="postgresql://zerve:zerve@localhost:5433/zerve_test" pytest tests/test_postgres_functional.py -v  # 29 tests

# All tests
DATABASE_URL="postgresql://zerve:zerve@localhost:5433/zerve_test" pytest tests/ -v

# Linting
flake8 . --max-line-length=127
```

---

## Architecture

The backend follows a **4-layer pattern** inspired by clean architecture:

```
HTTP Request
  --> Controller    (thin HTTP layer: parse request, extract params, call manager)
    --> Manager     (business logic: validation, queries, orchestration)
      --> Service   (third-party integrations: AI, Stripe, email, Cognito, S3)
        --> DatabaseService  (repository pattern with pluggable backends)
          --> DynamoDB repositories  OR  PostgreSQL repositories
  <-- ResponseModel (standardized: {success, data, message, error, status_code})
```

### Database Abstraction Layer

The backend uses a **Repository Pattern** with pluggable database backends. All managers access data through `self._db` (a `DatabaseService` instance) instead of calling DynamoDB directly.

```python
# In any manager:
user = self._db.users.get_by_id("user-123")
entries = self._db.time_entries.find_by_user_date_range(uid, start, end)
self._db.organizations.create(org_item)
```

The `DB_TYPE` environment variable controls which backend is used:

| DB_TYPE | Backend | When to use |
|---------|---------|-------------|
| `dynamodb` (default) | DynamoDB via boto3 | Production (Lambda), dev with AWS creds |
| `postgres` | PostgreSQL via SQLAlchemy | Local dev, self-hosted, testing |

**Key components:**

| Component | Path | Purpose |
|-----------|------|---------|
| `DatabaseService` | `services/database/DatabaseService.py` | Reads `DB_TYPE`, creates connector + all repositories |
| Repository interfaces | `database/repositories/interfaces/` | `IRepository[T]`, `IUserRepository`, `ITimeEntryRepository`, etc. |
| DynamoDB repos | `database/repositories/dynamodb/` | boto3-based implementations |
| PostgreSQL repos | `database/repositories/postgres/` | SQLAlchemy ORM implementations |
| SQLAlchemy models | `database/repositories/postgres/models.py` | ORM models for all 16 entities |
| Schemas | `database/schemas/` | 16 `@dataclass` schemas shared by both backends |

### How a request flows through the code

Example: `GET /api/organizations/members`

1. **`handler.py`** (Lambda only) strips the `/dev` stage prefix, fills in missing `sourceIp`
2. **Flask** routes the request to the registered endpoint
3. **`OrganizationController.list_members()`** validates the JWT via `@token_required`, creates a `RequestResourceModel(data={"action": "list_members"}, user_id=<cognito-sub>)`
4. **`OrganizationResourceManager._list_members()`** looks up the user via `self._db.users.get_by_id()`, queries members via `self._db.users.find_by("org_id", ...)`, maps results through `UserItem.to_api_dict()`
5. Returns `ResponseModel(success=True, data={"members": [...]})`
6. Controller calls `jsonify(result.to_dict())` and returns with the status code

### Abstractions (Base Classes)

| Class | File | Purpose |
|-------|------|---------|
| `IController` | `abstractions/IController.py` | `register_all_routes()`, `register_route(rule, endpoint, func, method)` |
| `IResourceManager` | `abstractions/IResourceManager.py` | `get()`, `post()`, `put()`, `delete()` -- all take `RequestResourceModel`, return `ResponseModel` |
| `IServiceManagerBase` | `abstractions/IServiceManagerBase.py` | `initialize()` -- called once at startup |
| `IOAuthProvider` | `abstractions/IOAuthProvider.py` | `get_authorization_url()`, `exchange_code_for_tokens()`, `get_user_info()` |
| `IStorageManager` | `abstractions/IStorageManager.py` | `upload_file()`, `download_file()`, `delete_file()` |
| `RequestResourceModel` | `abstractions/models/` | `data: dict`, `user_id: UUID` |
| `ResponseModel` | `abstractions/models/` | `success`, `data`, `message`, `error`, `status_code` |
| `StatusEnums` | `abstractions/enumerations/` | OrgRole, ProjectStatus, TimeEntrySource, ApprovalStatus, etc. |

### How controllers and managers are wired together

In `run_web_service.py`, `create_app()` does the following:

1. Initializes `DatabaseService` (reads `DB_TYPE` env var)
2. Initializes 9 services (Email, AI, Storage, Cognito, Stripe, Notification, Export, OAuth, Parsing)
3. Bundles them into a `service_managers` dict (including `"db": database_service`)
4. Creates 16 resource managers, each receiving `service_managers`
5. Calls `register_controller(app, ControllerClass, manager)` for each pair

```python
# Example from run_web_service.py
service_managers = {"db": db_service, "email": email_service, "ai": ai_service, ...}
org_manager = OrganizationResourceManager(service_managers=service_managers)
register_controller(app, OrganizationController, org_manager)
```

Managers access the database via `self._db` (shortcut for `self._service_managers["db"]`) and other services via `self._service_managers.get("service_name")`.

---

## Controllers (16)

| Controller | Routes | Description |
|-----------|--------|-------------|
| **AuthController** | `/api/auth/*` | Login, register, OAuth, password reset, invitation acceptance |
| **UserController** | `/api/users/*` | User CRUD, preferences, role updates |
| **OrganizationController** | `/api/organizations/*` | Org CRUD, invitations, member management |
| **ProjectController** | `/api/projects/*` | Project and task CRUD, budgets |
| **ClientController** | `/api/clients/*` | Client CRUD, client-project associations |
| **TimeEntryController** | `/api/time-entries/*` | Time entries, timer start/stop, calendar views, narratives |
| **TimesheetController** | `/api/timesheets/*` | Weekly timesheets, submit/approve/reject |
| **ReportController** | `/api/reports/*` | Summary, by-project, by-user, utilization, budget, export |
| **DashboardController** | `/api/dashboard/*` | Personal, team, and org dashboards |
| **AIChatController** | `/api/ai/*` | Chat sessions, messages, model config |
| **BillingController** | `/api/billing/*` | Stripe checkout, subscriptions, portal |
| **NotificationController** | `/api/notifications/*` | List, mark read, unread count |
| **SuperAdminController** | `/api/super-admin/*` | Global admin: list orgs/users, stats, toggle users |
| **ConfigController** | `/api/config/*` | Theme config, system settings |
| **AuditController** | `/api/audit/*` | Audit log retrieval |
| **AdminController** | `/api/admin/*` | Legacy stub (no-op) |

## Services (10)

| Service | File | Purpose |
|---------|------|---------|
| **DatabaseService** | `services/database/DatabaseService.py` | Repository-based DB access (DynamoDB or PostgreSQL) |
| **EmailService** | `services/email/EmailService.py` | SMTP email (invitations, password reset, reminders) |
| **AIService** | `services/ai/AIService.py` | Anthropic Claude + OpenAI for chat analytics, model registry |
| **UserService** | `services/user/UserService.py` | Cognito admin ops (create user, reset password, disable) |
| **StripeService** | `services/stripe/StripeService.py` | Checkout sessions, subscriptions, customer portal |
| **S3StorageService** | `services/storage/S3StorageService.py` | S3 upload/download |
| **LocalStorageService** | `services/storage/LocalStorageService.py` | Filesystem fallback when no S3 bucket |
| **NotificationService** | `services/notification/NotificationService.py` | In-app notification creation |
| **ExportService** | `services/export/ExportService.py` | CSV/PDF report generation |
| **FileParsingService** | `services/parsing/FileParsingService.py` | Uploaded file text extraction |
| **OAuthManager** | `services/oauth/OAuthManager.py` | Provider registry (Google impl, Azure AD scaffold) |

## Authentication

- **Cognito JWT** -- All protected endpoints require a `Bearer <token>` header
- Token is validated via Cognito JWKS (RS256) in `utils/auth_utils.py`
- `@token_required` decorator extracts `user_id` (Cognito `sub`) from the JWT
- `@org_role_required(*roles)` and `@super_admin_required` decorators in `utils/rbac_utils.py`
- **OAuth** -- Google Sign-In flow: frontend gets auth URL -> user authorizes -> backend exchanges code for tokens
- **Multi-tenant** -- `X-Org-Id` header on every API request for org-scoped data access

---

## Database Tables (16)

Both DynamoDB and PostgreSQL backends share the same 16 entity schemas defined as `@dataclass` classes in `database/schemas/`.

### Entity Relationship Diagram

```mermaid
erDiagram
    users {
        string id PK "Cognito sub"
        string email "GSI: EmailIndex"
        string org_id FK "GSI: OrgIdIndex"
        string org_role "owner|admin|manager|member"
        boolean is_super_admin
        string status "GSI: StatusIndex"
    }

    organizations {
        string id PK
        string slug "GSI: SlugIndex"
        string owner_id FK "GSI: OwnerIdIndex"
        string plan_tier
        string stripe_customer_id "GSI: StripeCustomerIndex"
        int member_count
    }

    org_invitations {
        string id PK
        string org_id FK "GSI: OrgIdIndex"
        string email "GSI: EmailIndex"
        string token "GSI: TokenIndex"
        string status
        int expires_at_ttl "TTL"
    }

    clients {
        string org_id PK
        string id SK
        string name "GSI: NameIndex"
    }

    projects {
        string org_id PK
        string id SK
        string code "GSI: CodeIndex"
        string client_id FK "GSI: ClientIdIndex"
        string parent_id FK "GSI: ParentIndex"
        string status "GSI: StatusIndex"
    }

    tasks {
        string org_id PK
        string id SK
        string project_id FK "GSI: ProjectIdIndex"
        int sort_order
    }

    time_entries {
        string org_id PK
        string id SK
        string user_id FK "GSI: UserDateIndex"
        string project_id FK "GSI: ProjectDateIndex"
        string client_id FK "GSI: ClientDateIndex"
        string date
        int duration_minutes
        string is_running "GSI: RunningTimerIndex"
        string approval_status "GSI: ApprovalIndex"
    }

    preset_narratives {
        string org_id PK
        string id SK
        string user_id FK "GSI: UserIdIndex"
        string project_id FK "GSI: ProjectIdIndex"
    }

    timesheets {
        string org_id PK
        string user_week SK
        string user_id FK "GSI: UserIdIndex"
        string status "GSI: StatusIndex"
    }

    notifications {
        string user_id PK
        string timestamp_id SK
        string org_id FK "GSI: OrgIdIndex"
        int expires_at_ttl "TTL"
    }

    ai_chat_sessions {
        string user_id PK
        string id SK
        string org_id FK "GSI: OrgIdIndex"
    }

    ai_chat_messages {
        string session_id PK
        string timestamp_id SK
    }

    subscription_plans {
        string id PK
    }

    integrations {
        string org_id PK
        string provider_id SK
    }

    config {
        string pk PK
        string sk SK
    }

    audit_log {
        string id PK
        string timestamp SK
        string user_id FK "GSI: UserIdIndex"
        string org_id FK "GSI: OrgIdIndex"
    }

    organizations ||--o{ users : "has members"
    organizations ||--o{ org_invitations : "sends"
    organizations ||--o{ clients : "manages"
    organizations ||--o{ projects : "contains"
    organizations ||--o{ tasks : "contains"
    organizations ||--o{ time_entries : "tracks"
    organizations ||--o{ timesheets : "reviews"
    organizations ||--o{ notifications : "notifies"
    organizations ||--o{ integrations : "configures"
    organizations ||--o{ preset_narratives : "defines"
    organizations ||--o{ ai_chat_sessions : "uses"
    organizations }o--|| subscription_plans : "subscribes to"
    users ||--o{ time_entries : "logs"
    users ||--o{ timesheets : "submits"
    users ||--o{ notifications : "receives"
    users ||--o{ ai_chat_sessions : "creates"
    users ||--o{ audit_log : "generates"
    projects ||--o{ tasks : "has"
    projects ||--o{ time_entries : "receives entries"
    clients ||--o{ projects : "owns"
    ai_chat_sessions ||--o{ ai_chat_messages : "contains"
```

### Schema Conventions

- All schemas are Python `@dataclass` classes in `database/schemas/`
- Each implements `to_item()` (Python -> dict), `from_item(dict)` (dict -> Python), `to_api_dict()` (Python -> camelCase JSON for frontend)
- Schemas are shared by both DynamoDB and PostgreSQL backends
- `is_running` on time entries is stored as string `"true"/"false"` because DynamoDB GSI keys must be String/Number/Binary

---

## Project Structure

```
backend/
  abstractions/
    IController.py                  # Base: register_all_routes(), register_route()
    IResourceManager.py             # Base: get(), post(), put(), delete()
    IServiceManagerBase.py          # Base: initialize()
    IOAuthProvider.py               # Base: OAuth provider interface
    IStorageManager.py              # Base: upload/download/delete file
    enumerations/StatusEnums.py     # OrgRole, ProjectStatus, ApprovalStatus, etc.
    models/
      RequestResourceModel.py       # Input wrapper: {data, user_id}
      ResponseModel.py              # Output wrapper: {success, data, message, error}
  controllers/                      # 16 controllers (thin HTTP layer)
    auth/AuthController.py
    users/UserController.py
    organizations/OrganizationController.py
    projects/ProjectController.py
    clients/ClientController.py
    time_entries/TimeEntryController.py
    timesheets/TimesheetController.py
    reports/ReportController.py
    dashboard/DashboardController.py
    ai_chat/AIChatController.py
    billing/BillingController.py
    notifications/NotificationController.py
    super_admin/SuperAdminController.py
    config/ConfigController.py
    audit/AuditController.py
    admin/AdminController.py        # Legacy stub
  managers/                         # 16 managers (mirrors controllers/)
    auth/AuthResourceManager.py     # Register, login, OAuth, password flows
    users/UserResourceManager.py    # User CRUD, role updates
    organizations/OrganizationResourceManager.py  # Org CRUD, members, invites
    projects/ProjectResourceManager.py
    clients/ClientResourceManager.py
    time_entries/TimeEntryResourceManager.py      # Timer start/stop, calendar views
    timesheets/TimesheetResourceManager.py        # Submit, approve, reject
    reports/ReportResourceManager.py              # Analytics, export
    dashboard/DashboardResourceManager.py
    ai_chat/AIChatResourceManager.py              # Claude chat sessions
    billing/BillingResourceManager.py             # Stripe checkout/subscriptions
    notifications/NotificationResourceManager.py
    super_admin/SuperAdminResourceManager.py
    config/ConfigResourceManager.py
    audit/AuditResourceManager.py
    admin/AdminResourceManager.py   # Stub
  services/
    database/
      DatabaseService.py            # Repository-based DB access (reads DB_TYPE env var)
    ai/AIService.py                 # Anthropic Claude + OpenAI, model registry
    email/EmailService.py           # SMTP email (invitations, password reset)
    storage/
      S3StorageService.py           # AWS S3 uploads
      LocalStorageService.py        # Filesystem fallback
    user/UserService.py             # Cognito admin operations
    stripe/StripeService.py         # Stripe payments
    notification/NotificationService.py
    export/ExportService.py         # CSV/PDF generation
    parsing/FileParsingService.py
    oauth/
      OAuthManager.py               # Provider registry
      GoogleOAuthService.py          # Google OAuth implementation
      AzureADOAuthService.py         # Azure AD scaffold
  database/
    db.py                           # Init entry point
    dynamodb.py                     # Legacy get_table() -- still used by utils/ and services/, pending migration
    schemas/                        # 16 @dataclass schemas (shared by both backends)
      user.py, organization.py, org_invitation.py, project.py,
      client.py, time_entry.py, timesheet.py, task.py,
      preset_narrative.py, ai_chat_session.py, ai_chat_message.py,
      notification.py, audit_log.py, subscription_plan.py,
      integration.py, config.py
    repositories/
      interfaces/                   # Abstract interfaces for all repositories
        IRepository.py              # Generic IRepository[T] base
        IUserRepository.py          # find_by_email, update_fields, scan_count
        ITimeEntryRepository.py     # find_by_user_date_range, find_running_timer
        ITimesheetRepository.py     # find_by_org_user_week, find_by_org_status
        IConfigRepository.py        # get_config, put_config
        IUserRoleRepository.py      # grant_role, revoke_role, is_super_admin
      dynamodb/                     # DynamoDB implementations (boto3)
        connector.py                # DynamoDBConnector (table prefix, boto3 resource)
        base_repository.py          # Generic DynamoDBRepository[T]
        user_repository.py          # DynamoDB-specific user queries
        time_entry_repository.py
        timesheet_repository.py
        config_repository.py
        user_role_repository.py
      postgres/                     # PostgreSQL implementations (SQLAlchemy)
        connector.py                # PostgresConnector (engine, sessionmaker)
        models.py                   # SQLAlchemy ORM models for all 16 entities
        base_repository.py          # Generic PostgresRepository[T]
        user_repository.py
        time_entry_repository.py
        timesheet_repository.py
        config_repository.py
        user_role_repository.py
  config/
    model_registry.py               # LLM models: GPT-4o, Claude Sonnet, etc.
  utils/
    auth_utils.py                   # @token_required, Cognito JWKS JWT validation
    rbac_utils.py                   # @org_role_required, @super_admin_required
    encryption.py                   # Fernet symmetric encryption
    register_components.py          # register_controller() helper
  handler.py                        # AWS Lambda entry point (apig-wsgi wrapper)
  run_web_service.py                # Flask app factory + local dev server
  requirements.txt                  # Production dependencies
  requirements-dev.txt              # Test dependencies (pytest, etc.)
  tests/                            # Unit + functional tests
    test_postgres_functional.py     # 29 PostgreSQL functional tests (requires Docker)
    conftest.py                     # Shared fixtures, custom markers
  .env                              # Local config (gitignored)
  .venv/                            # Virtual environment (gitignored)
```

## API Endpoints

### Auth (`/api/auth/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | Public | Register new user |
| POST | `/api/auth/login` | Public | Login and get JWT |
| POST | `/api/auth/logout` | JWT | Logout |
| POST | `/api/auth/refresh` | JWT | Refresh token |
| POST | `/api/auth/forgot-password` | Public | Request password reset |
| POST | `/api/auth/reset-password` | Public | Reset password with code |
| POST | `/api/auth/challenge` | Public | Respond to NEW_PASSWORD_REQUIRED |
| POST | `/api/auth/accept-invitation` | Optional | Accept org invitation by token |
| GET | `/api/auth/oauth/:provider/authorize` | Public | Get OAuth authorization URL |
| POST | `/api/auth/oauth/:provider/callback` | Public | Exchange OAuth code for tokens |

### Time Entries (`/api/time-entries/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/time-entries` | List entries (filters: start_date, end_date, project_id, user_id) |
| POST | `/api/time-entries` | Create manual entry |
| POST | `/api/time-entries/bulk` | Bulk create entries |
| GET | `/api/time-entries/:id` | Get single entry |
| PUT | `/api/time-entries/:id` | Update entry |
| DELETE | `/api/time-entries/:id` | Delete entry |
| POST | `/api/time-entries/timer/start` | Start timer |
| POST | `/api/time-entries/timer/stop` | Stop timer |
| GET | `/api/time-entries/timer/current` | Get running timer |
| DELETE | `/api/time-entries/timer/discard` | Discard running timer |
| GET | `/api/time-entries/day/:date` | Day view |
| GET | `/api/time-entries/week/:date` | Week view |
| GET | `/api/time-entries/month/:year/:month` | Month view |

### Other endpoints

See the controller files in `controllers/` for full route definitions for Projects, Clients, Timesheets, Reports, Dashboard, AI Chat, Billing, Notifications, and Super Admin.
