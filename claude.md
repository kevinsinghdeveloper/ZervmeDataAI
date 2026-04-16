# Claude Code Instructions - Zerve App

## Quick Commands

```bash
# Frontend
cd frontend && npm install && npm start    # Dev server on http://localhost:3000

# Backend
cd backend && pip install -r requirements.txt && python run_web_service.py  # API on http://localhost:8000

# Full stack (Docker)
docker-compose up --build    # Frontend :3000, Backend :8000, PostgreSQL :5432
```

## Project Structure

```
zerve-app/
  frontend/                # React 18 + TypeScript + MUI + Tailwind
    src/
      components/
        context_providers/ # React Context (Auth, User, RBAC, Theme, Documents, Notification)
        pages/             # Page components
        shared/            # Shared components (Header, Footer, ProtectedRoute, LoadingSpinner)
      utils/               # API service layer (Axios)
      configs/             # API endpoints configuration
      types/               # TypeScript type definitions
      theme/               # MUI theme configuration
  backend/                 # Flask + SQLAlchemy + LangChain
    abstractions/          # Base classes (IController, IResourceManager, IServiceManagerBase)
    controllers/           # HTTP route handlers (thin layer)
    managers/              # Business logic (resource managers)
    services/              # Third-party integrations (AI, storage, email, processing)
    database/              # SQLAlchemy models and DB setup
    config/                # AI model registry
    utils/                 # Auth, encryption, registration utilities
  infrastructure/          # Terraform IaC
    terraform/aws/         # AWS: S3, CloudFront, API Gateway, Cognito, DynamoDB, Lambda
  .github/workflows/       # CI/CD: lint, test, build, deploy
  scripts/                 # Deployment automation
```

## Architecture Patterns

### Frontend (from FE-ToStructured)
- **State Management**: React Context API (NOT Redux/Zustand)
- **Contexts**: AuthContext, UserContext, RBACContext, ThemeConfigContext, DocumentContext, NotificationContext
- **UI Library**: Material-UI v5 with dark theme + Tailwind CSS utilities
- **API Layer**: Singleton Axios service with Bearer token injection and 401 auto-redirect
- **Routing**: React Router v6 with `<ProtectedRoute>` wrapper and `adminOnly` prop

### Backend (from BE-ToStructured)
- **Architecture**: 4-layer pattern
  1. **Controllers** - Parse HTTP requests, delegate to managers
  2. **Managers** (Resource Managers) - Business logic, DB transactions via `self._db`
  3. **Services** - Third-party integrations (AI, storage, email, database)
  4. **Abstractions** - Base classes and interfaces
- **Request/Response**: `RequestResourceModel` (data + user_id) -> `ResponseModel` (success, data, message, error)
- **Auth**: JWT tokens with `@token_required` decorator
- **Database**: Repository pattern with pluggable backends (`DB_TYPE` env var)
  - `dynamodb` (default) - DynamoDB via boto3 (production/Lambda)
  - `postgres` - PostgreSQL via SQLAlchemy ORM (local dev, self-hosted)
  - All managers use `self._db.{repo}.method()` -- never call `get_table()` directly
  - 16 shared `@dataclass` schemas in `database/schemas/`
  - 5 specialized + 11 generic repositories per backend

### Infrastructure (from consulting-react-template)
- **IaC**: Terraform for AWS (Cognito, API Gateway, S3, CloudFront, DynamoDB)
- **CI/CD**: GitHub Actions (lint, test, build, security scan, deploy)
- **Security**: npm audit, pip audit, secret detection, CORS, JWT auth

## Coding Conventions

### Frontend
- Context providers in `src/components/context_providers/`
- Page components in `src/components/pages/`
- Shared components in `src/components/shared/`
- Custom hooks via `useAuth()`, `useUser()`, `useRBAC()`, `useDocuments()`, `useNotification()`, `useThemeConfig()`
- Types in `src/types/index.ts`
- API methods in `src/utils/api.service.ts`

### Backend
- Every controller extends `IController` with `register_all_routes()` and `get_resource_manager()`
- Every manager extends `IResourceManager` with `get()`, `post()`, `put()`, `delete()`
- Every service extends `IServiceManagerBase` with `initialize()`
- Use `register_controller(app, ControllerClass, resource_manager)` to register routes
- Managers access DB via `self._db` (DatabaseService) -- e.g. `self._db.users.get_by_id()`, `self._db.time_entries.create()`
- Never import `get_table` from `database.dynamodb` in managers -- use repository methods
- Audit log all destructive actions (create, update, delete)

### Styling
- MUI theme: dark mode, primary #7b6df6 (purple), secondary #10b981 (green)
- Tailwind CSS for utility classes
- CSS variables in `src/index.css`

## Key Files to Edit

| Task | File(s) |
|------|---------|
| Add a new page | Create in `frontend/src/components/pages/`, add route in `App.tsx` |
| Add API endpoint | Create controller in `backend/controllers/`, manager in `backend/managers/` |
| Add DB model | Create schema in `backend/database/schemas/`, add SQLAlchemy model in `database/repositories/postgres/models.py`, add repo in `DatabaseService` |
| Change theme | Edit `frontend/src/theme/theme.ts` and `tailwind.config.js` |
| Add context | Create in `frontend/src/components/context_providers/`, wrap in `App.tsx` |
| Add AI provider | Edit `backend/services/ai/` and `backend/config/model_registry.py` |
| Modify infra | Edit files in `infrastructure/terraform/aws/` |

## RBAC Roles

| Role | Access |
|------|--------|
| **admin** | Full access to everything |
| **editor** | Create/edit content, documents, pipelines |
| **viewer** | Read-only access |

First registered user automatically becomes admin.

## Environment Variables

See `.env.example` for all available configuration options.

## Testing

```bash
# Frontend
cd frontend && npm test

# Backend unit tests (no external deps, runs in CI)
cd backend && pytest tests/ -m "not postgres" -v    # 269 tests

# Backend PostgreSQL functional tests (requires Docker)
sudo docker compose -f docker-compose.test.yml up -d
cd backend && DATABASE_URL="postgresql://zerve:zerve@localhost:5433/zerve_test" pytest tests/test_postgres_functional.py -v  # 29 tests

# Security
cd frontend && npm audit
pip-audit -r backend/requirements.txt
```



# Zerve My Time – Final Project Instructions

### Project is bascially a time tracking app similar to Harvest

We will have the following -

- Organizations and their users
- Organization roles and global app admin to manage orgs and users
- Advance time tracking
  - Nice calendar view -- day, week, month
  - Multiple projects with sub projects can assign a project id, description
  - users can use present narratives and track time
  - an org role that can create projects etc... 
  - org role to pull extracts of data, view charts and has dashboard
  - ai chat which can show charts and perform analysis -- also reach support
  - global admin console to configure things -- preserve some of what we have like themes and chat bot etc.

## Checkpoint Logs

When asked for a "checkpoint log", create a timestamped markdown file at `docs/checkpoints/YYYY-MM-DD-HHMMSS.md` documenting all changes made in the current session — files created/modified, features added, tests affected, and any open items or next steps.
