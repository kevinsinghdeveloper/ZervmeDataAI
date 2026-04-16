# ZerveMeDataAI

A production-grade, multi-tenant **AI competitive intelligence platform** built with React, Flask, and AWS serverless infrastructure. Designed for research teams to run LLM-powered ETL pipelines, generate competitive analysis reports, and visualize insights through dynamic dashboards.

---

## Key Features

### AI-Powered Report Pipeline
- Pluggable ETL engine with dynamic report discovery
- LLM-driven data extraction, transformation, and analysis
- Multi-provider AI support (OpenAI GPT-4, extensible to others)
- DynamoDB-backed result caching with file-based fallback

### Projects & Reports
- Organize research by project (Competitive Intelligence, Market Research, etc.)
- Create reports with configurable datasets and model parameters
- Full CRUD lifecycle for projects, reports, datasets, and model configs

### Job Tracking
- Real-time job lifecycle management (pending, running, completed, failed)
- Persistent job records with error reporting and result storage
- Start, monitor, and stop ETL jobs via REST API

### Dynamic Dashboards
- Template-driven report rendering (text, tables, charts, grids)
- Recharts-powered visualizations (bar, line, pie, radar)
- Per-report dashboard with overview statistics

### Organizations & RBAC
- Multi-tenant architecture with org-level data isolation
- Users can belong to multiple organizations with different roles
- 4-tier role hierarchy: **Owner > Admin > Manager > Member**
- Permission-based access: `view_projects`, `manage_projects`, `manage_users`, `view_reports`, `manage_org`

### AI Chat
- Chat-based analytics assistant powered by Anthropic Claude
- Natural language queries with conversation history
- Multi-model support with configurable model registry

### Authentication
- AWS Cognito with RS256 JWT validation via JWKS
- Google OAuth single sign-in
- Email verification, password reset, and invitation-based onboarding

---

## Architecture

```
                      ┌─────────────────┐
                      │   CloudFront    │
                      │   CDN + SPA     │
                      └────────┬────────┘
                               │
                      ┌────────┴────────┐
                      │    S3 Bucket    │
                      │  (React Build)  │
                      └─────────────────┘

Users ──► API Gateway (HTTP) ──► Lambda (Flask) ──► DatabaseService
                                      │                  ├── DynamoDB (15 tables)
                                      │                  └── PostgreSQL (via SQLAlchemy)
                                      ├── Cognito (Auth + JWT)
                                      ├── SES (Transactional Email)
                                      ├── S3 (File Uploads)
                                      ├── ETLService (Report Pipeline)
                                      └── OpenAI / Anthropic (AI)
```

### Backend: 4-Layer Pattern

```
Controllers (HTTP routing)
    └── Resource Managers (Business logic)
            └── Services (3rd-party integrations)
                    └── DatabaseService (Repository pattern, pluggable backends)
```

- **16 Controllers** — Auth, User, Organization, Project, Report, ReportProcessor, Dataset, ModelConfig, Dashboard, AIChat, Notification, Config, Audit, Admin, SuperAdmin, Documents
- **16 Resource Managers** — Encapsulate all business logic, testable in isolation
- **8 Services** — Database, Email (SES), User (Cognito), AI, ETL, Notification, OAuth, Storage
- **15 DynamoDB Tables** — All with point-in-time recovery, PAY_PER_REQUEST billing

### ETL Pipeline

```
ReportProcessorResourceManager
    └── ETLService (dynamic report discovery)
            ├── AIServiceHandler (LLM factory)
            │       └── OpenAIETLServiceManager (GPT-4)
            └── EtlReportBase (pipeline + caching)
                    ├── brand_power.py
                    └── competitor_tracker.py
```

### Frontend: Context-Driven Architecture

```
ThemeConfig > Notification > Auth > User > RBAC > Organization > Explorer
```

- **7 React Context Providers** — Nested in dependency order for clean state management
- **23 Page Components** — Full SPA with protected routing and role-based access
- **Singleton API Service** — Axios-based with automatic JWT injection and org-scoped headers

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Material-UI 5, Recharts |
| **Backend** | Python 3.12, Flask, apig-wsgi (Lambda adapter) |
| **Database** | Amazon DynamoDB (production) / PostgreSQL (self-hosted) |
| **Auth** | AWS Cognito, RS256 JWT, Google OAuth 2.0 |
| **Email** | Amazon SES with custom domain (DKIM/SPF) |
| **Storage** | Amazon S3 (AES-256 encrypted, versioned) |
| **CDN** | Amazon CloudFront (HTTP/2+3, OAC, custom domain + ACM cert) |
| **API** | Amazon API Gateway HTTP (CORS, throttling, JWT authorizer) |
| **Compute** | AWS Lambda (Python 3.12, 256MB) |
| **AI** | OpenAI GPT-4, Anthropic Claude (multi-provider) |
| **IaC** | Terraform (full AWS stack) |
| **CI/CD** | GitHub Actions (lint, test, build, security scan, deploy) |

---

## Database Design

15 DynamoDB tables with a pluggable repository pattern that also supports PostgreSQL:

| Table | Key Schema | Purpose |
|-------|-----------|---------|
| `users` | `id` | User profiles, preferences, OAuth providers |
| `user_roles` | `user_id` + `org_role` | Multi-org role assignments |
| `organizations` | `id` | Tenant profiles, plan tiers |
| `org_invitations` | `id` | Token-based invitations with 7-day TTL |
| `projects` | `org_id` + `id` | AI research projects with type and description |
| `reports` | `org_id` + `id` | Report definitions with dataset and model config |
| `report_jobs` | `org_id` + `id` | ETL job execution records and results |
| `report_cache` | `report_id` + `cache_key` | Cached ETL results with TTL |
| `datasets` | `org_id` + `id` | Dataset configurations and domain data |
| `model_configs` | `org_id` + `id` | AI model configurations |
| `notifications` | `user_id` + `timestamp_id` | In-app notifications with 90-day TTL |
| `ai_chat_sessions` | `user_id` + `id` | Chat session metadata |
| `ai_chat_messages` | `session_id` + `timestamp_id` | Message history with chart configs |
| `audit_log` | `id` + `timestamp` | Full audit trail of actions |
| `config` | `pk` + `sk` | System settings, AI model configs |

---

## API Endpoints

| Endpoint | Methods | Purpose |
|----------|---------|---------|
| `/api/health` | GET | Health check |
| `/api/auth/*` | POST | Login, register, verify, reset password |
| `/api/projects` | GET, POST | List/create AI projects |
| `/api/projects/<id>` | GET, PUT, DELETE | Project CRUD |
| `/api/reports` | GET, POST | List/create reports |
| `/api/reports/<id>` | GET, PUT, DELETE | Report CRUD |
| `/api/report-processor` | POST | Start/stop ETL jobs |
| `/api/report-processor/status` | GET | Check job status |
| `/api/dashboard/report/<id>` | GET | Dashboard data for a report |
| `/api/dashboard/overview` | GET | Platform-wide statistics |
| `/api/datasets` | GET, POST | List/create datasets |
| `/api/datasets/<id>` | GET, PUT, DELETE | Dataset CRUD |
| `/api/model-configs` | GET, POST | List/create model configs |
| `/api/model-configs/<id>` | GET, PUT, DELETE | Model config CRUD |
| `/api/ai-chat/*` | GET, POST | AI chat sessions and messages |
| `/api/organizations/*` | GET, POST, PUT | Organization management |
| `/api/users/*` | GET, PUT | User management |

---

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker (for DynamoDB Local)

### Quick Start

```bash
# 1. Start DynamoDB Local
docker compose up -d dynamodb-local

# 2. Backend
cd backend
pip install -r requirements.txt
python run_web_service.py
# API running at http://localhost:8000

# 3. Frontend
cd frontend
npm install
npm start
# App running at http://localhost:3000
```

### Environment Variables

Backend (`backend/.env`):
```env
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
FLASK_DEBUG=true
DB_TYPE=dynamodb
DYNAMODB_ENDPOINT_URL=http://localhost:8001
OPENAI_API_KEY=<your-key>
CORS_ORIGINS=http://localhost:3000
```

Frontend (`frontend/.env`):
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

---

## Testing

```bash
# Backend: 323 unit tests
cd backend && pytest tests/ -m "not postgres" -v

# Backend: PostgreSQL integration tests
docker compose -f docker-compose.test.yml up -d
DATABASE_URL="postgresql://zerve:zerve@localhost:5433/zerve_test" \
  pytest tests/test_postgres_functional.py -v

# Frontend: 102 unit tests
cd frontend && npm test -- --watchAll=false

# Frontend: production build
cd frontend && CI=true npm run build
```

---

## Project Structure

```
ZerveMeDataAI/
├── frontend/                       # React 18 + TypeScript SPA
│   └── src/
│       ├── components/
│       │   ├── context_providers/  # 7 React Contexts (Auth, RBAC, Org, Explorer, etc.)
│       │   ├── pages/              # 23 page components
│       │   └── shared/             # DynamicReportRenderer, Header, Footer, etc.
│       ├── utils/                  # API service layer (Axios singleton)
│       ├── types/                  # TypeScript type definitions + report templates
│       └── theme/                  # MUI dark theme configuration
├── backend/                        # Flask API (runs on Lambda)
│   ├── controllers/                # 16 HTTP route handlers
│   ├── managers/                   # 16 business logic managers
│   ├── services/                   # 8 third-party integration services
│   ├── report_etls/                # ETL pipeline modules (brand_power, competitor_tracker)
│   │   └── report_resources/       # Static data (industries, sources)
│   ├── database/
│   │   ├── schemas/                # 14 dataclass schemas
│   │   └── repositories/          # DynamoDB + SQLAlchemy connectors
│   ├── abstractions/               # Base classes (IResourceManager, EtlReportBase, etc.)
│   ├── models/                     # Request/response models (LLM, ReportProcessor)
│   ├── utility/                    # Logging, JSON helpers
│   └── tests/                      # 323 unit tests + integration tests
├── infrastructure/
│   └── terraform/aws/              # Full AWS stack (Cognito, API GW, Lambda,
│                                   #   DynamoDB, S3, CloudFront, SES, IAM)
├── .github/workflows/ci.yml       # CI/CD pipeline
├── scripts/                        # Deployment automation
└── docker-compose.yml              # Local dev (DynamoDB Local, backend, frontend)
```

---

## Deployment

```bash
# Deploy AWS infrastructure via Terraform
./scripts/deploy-terraform-aws.sh <environment> <aws-profile> <region>

# Example
./scripts/deploy-terraform-aws.sh dev default us-east-1
```

---

## License

Private — All rights reserved.
