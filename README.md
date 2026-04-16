# Zerve My Time

A production-grade, multi-tenant **time tracking SaaS platform** built with React, Flask, and AWS serverless infrastructure. Designed for professional services teams to track billable hours, manage projects and clients, approve timesheets, generate reports and invoices, and leverage AI-powered analytics.

**Live Demo**: [time.zerveme.com](https://time.zerveme.com)

---

## Key Features

### Time Tracking
- Real-time timer with one-click start/stop or manual hour entry
- Day, week, and month calendar views
- Preset narratives for frequently used time descriptions
- Bulk import from CSV

### Projects & Clients
- Hierarchical projects with sub-projects and task breakdown
- Per-project billing rates, budgets (hours and dollar amounts), and color coding
- Client management with contact details and multi-project association

### Timesheets & Approvals
- Weekly timesheet submission with automatic hour aggregation
- Manager approval/rejection workflow with notes
- Team-wide timesheet overview for managers

### Reports & Invoicing
- 7 report types: Summary, By Project, By User, By Client, By Date, Utilization, Budget
- Export to CSV, Excel (XLSX), and PDF with professional formatting
- Invoice generation with line items, tax calculations, and branded PDF output

### Organizations & RBAC
- Multi-tenant architecture with org-level data isolation
- Users can belong to multiple organizations with different roles
- 4-tier role hierarchy: **Owner > Admin > Manager > Member**
- Global super admin console for platform-wide management

### AI Analytics
- Chat-based analytics assistant powered by Anthropic Claude
- Natural language queries against time tracking data
- Inline chart generation for visual analysis
- Multi-model support (Claude and GPT) with configurable model registry

### Billing
- Stripe-powered subscription management (Free, Starter, Professional, Enterprise)
- Self-service checkout and billing portal
- Webhook-driven plan tier updates

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
                                      │                  ├── DynamoDB (17 tables)
                                      │                  └── PostgreSQL (via SQLAlchemy)
                                      ├── Cognito (Auth + JWT)
                                      ├── SES (Transactional Email)
                                      ├── S3 (File Uploads)
                                      ├── Stripe (Billing)
                                      └── Anthropic Claude / OpenAI (AI)
```

### Backend: 4-Layer Pattern

```
Controllers (HTTP routing)
    └── Resource Managers (Business logic)
            └── Services (3rd-party integrations)
                    └── DatabaseService (Repository pattern, pluggable backends)
```

- **16 Controllers** — Auth, User, Organization, Project, Client, TimeEntry, Timesheet, Report, Dashboard, AI Chat, Billing, Notification, Config, Audit, Admin, Super Admin
- **16 Resource Managers** — Encapsulate all business logic, testable in isolation
- **9 Services** — Database, Email (SES), User (Cognito), AI, Stripe, Notification, Export, OAuth, Storage
- **17 DynamoDB Tables** — All with point-in-time recovery, PAY_PER_REQUEST billing

### Frontend: Context-Driven Architecture

```
ThemeConfig > Notification > Auth > User > RBAC > Organization > Project > TimeTracking
```

- **8 React Context Providers** — Nested in dependency order for clean state management
- **20+ Page Components** — Full SPA with protected routing and role-based access
- **Singleton API Service** — Axios-based with automatic JWT injection and org-scoped headers

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Material-UI 5, Tailwind CSS |
| **Backend** | Python 3.12, Flask, apig-wsgi (Lambda adapter) |
| **Database** | Amazon DynamoDB (production) / PostgreSQL (self-hosted) |
| **Auth** | AWS Cognito, RS256 JWT, Google OAuth 2.0 |
| **Email** | Amazon SES with custom domain (DKIM/SPF) |
| **Storage** | Amazon S3 (AES-256 encrypted, versioned) |
| **CDN** | Amazon CloudFront (HTTP/2+3, OAC, custom domain + ACM cert) |
| **API** | Amazon API Gateway HTTP (CORS, throttling, JWT authorizer) |
| **Compute** | AWS Lambda (Python 3.12, 256MB) |
| **Billing** | Stripe (Checkout, Subscriptions, Customer Portal, Webhooks) |
| **AI** | Anthropic Claude API, OpenAI API (multi-provider) |
| **IaC** | Terraform (full AWS stack) |
| **CI/CD** | GitHub Actions (lint, test, build, security scan, deploy) |
| **PDF/Excel** | ReportLab (PDF), openpyxl (XLSX) |

---

## Database Design

17 DynamoDB tables with a pluggable repository pattern that also supports PostgreSQL:

| Table | Key Schema | Purpose |
|-------|-----------|---------|
| `users` | `id` | User profiles, preferences, OAuth providers |
| `user_roles` | `user_id` + `org_role` | Multi-org role assignments (supports multiple roles per org) |
| `organizations` | `id` | Tenant profiles, Stripe customer linkage, plan tiers |
| `org_invitations` | `id` | Token-based invitations with 7-day TTL |
| `projects` | `org_id` + `id` | Projects with budgets, rates, sub-project hierarchy |
| `tasks` | `org_id` + `id` | Task breakdown within projects |
| `clients` | `org_id` + `id` | Client records with contacts |
| `time_entries` | `org_id` + `id` | Core entity — hours, timer state, billability, approval |
| `timesheets` | `org_id` + `user_week` | Weekly aggregation and approval status |
| `preset_narratives` | `org_id` + `id` | Reusable time entry descriptions |
| `notifications` | `user_id` + `timestamp_id` | In-app notifications with 90-day TTL |
| `ai_chat_sessions` | `user_id` + `id` | Chat session metadata |
| `ai_chat_messages` | `session_id` + `timestamp_id` | Message history with chart configs |
| `audit_log` | `id` + `timestamp` | Full audit trail of destructive actions |
| `subscription_plans` | `id` | Plan definitions and Stripe price linkage |
| `integrations` | `org_id` + `provider_id` | External integration configs (extensible) |
| `config` | `pk` + `sk` | System settings, theme, AI model configs |

All tables include GSIs for efficient query patterns (e.g., `UserDateIndex`, `ProjectDateIndex`, `RunningTimerIndex` on time_entries).

---

## CI/CD Pipeline

Automated via GitHub Actions on push to `main`:

1. **Frontend CI** — ESLint, TypeScript type-check, 153 unit tests, production build
2. **Backend CI** — flake8, 370 unit tests (pytest)
3. **Integration Tests** — PostgreSQL functional tests against a Docker container
4. **Security Scan** — npm audit + pip-audit
5. **Deploy Backend** — Package Lambda zip, upload to S3, update function code, smoke test `/api/health`
6. **Deploy Frontend** — Build with environment variables, sync to S3, invalidate CloudFront cache

---

## Testing

```bash
# Backend: 370 unit tests
cd backend && pytest tests/ -m "not postgres" -v

# Backend: 29 PostgreSQL integration tests
docker compose -f docker-compose.test.yml up -d
DATABASE_URL="postgresql://zerve:zerve@localhost:5433/zerve_test" \
  pytest tests/test_postgres_functional.py -v

# Frontend: 153 unit tests
cd frontend && npm test -- --watchAll=false

# Frontend: production build verification
cd frontend && CI=true npm run build
```

---

## Project Structure

```
zerve-app/
├── frontend/                    # React 18 + TypeScript SPA
│   └── src/
│       ├── components/
│       │   ├── context_providers/  # 8 React Contexts (Auth, RBAC, Org, etc.)
│       │   ├── pages/              # 20+ page components
│       │   └── shared/             # Header, Footer, ProtectedRoute, LoadingSpinner
│       ├── utils/                  # API service layer (Axios singleton)
│       ├── types/                  # TypeScript type definitions
│       └── theme/                  # MUI dark theme configuration
├── backend/                     # Flask API (runs on Lambda)
│   ├── controllers/             # 16 HTTP route handlers
│   ├── managers/                # 16 business logic managers
│   ├── services/                # 9 third-party integration services
│   ├── database/
│   │   ├── schemas/             # 17 dataclass schemas
│   │   └── repositories/       # DynamoDB + SQLAlchemy connectors
│   ├── utils/                   # Auth, RBAC, encryption utilities
│   └── tests/                   # 370+ unit tests + integration tests
├── infrastructure/
│   └── terraform/aws/           # Full AWS stack (Cognito, API GW, Lambda,
│                                #   DynamoDB, S3, CloudFront, SES, IAM)
├── .github/workflows/ci.yml    # CI/CD pipeline
└── scripts/                     # Deployment automation
```

---

## License

Private — All rights reserved.
