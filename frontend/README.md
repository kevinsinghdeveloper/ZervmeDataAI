# Frontend -- React SPA

The frontend is a single-page application built with React 18, TypeScript, Material UI 5, and Tailwind CSS. It communicates with the Flask backend via a singleton Axios API service and manages state through 8 React Context providers.

## Local Development

### Prerequisites

- Node.js 20+

### Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Create .env
cat > .env <<EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_COGNITO_REGION=us-east-1
REACT_APP_COGNITO_USER_POOL_ID=us-east-1_R7LaDuCWI
REACT_APP_COGNITO_CLIENT_ID=1259agca7ctc1fbuglifa6tr1i
EOF

# 3. Start dev server
npm start                        # http://localhost:3000
```

### Point at the deployed API (no local backend needed)

```bash
# In frontend/.env, change API_URL:
REACT_APP_API_URL=https://pr907093ub.execute-api.us-east-1.amazonaws.com/dev
```

### Running tests

```bash
npm test                         # Interactive watch mode
npm test -- --watchAll=false     # Single run (CI mode)
CI=true npm run build            # Production build (warnings = errors)
```

---

## Architecture

### How the app boots

1. `index.tsx` renders `<App />` wrapped in `<BrowserRouter>`
2. `App.tsx` nests 8 context providers (see below) and defines all routes
3. On mount, `AuthContext` checks localStorage for a saved JWT token
4. If authenticated, `UserContext` fetches the user profile from `/api/users/me`
5. `RBACContext` derives permissions from the user's `orgRole` and `isSuperAdmin`
6. `OrganizationContext` fetches the current org details
7. `ProjectContext` and `TimeTrackingContext` load org-scoped data
8. The router renders the appropriate page inside `AppLayout` (sidebar + top bar)

### Context Providers (State Management)

The app uses React Context API (not Redux). Providers are nested in `App.tsx` in this order -- each inner provider can access all outer providers:

```
ThemeConfigProvider              # Dynamic theme colors, logo, branding
  > NotificationProvider         # Toast notifications (showSuccess, showError, showInfo, showWarning)
    > AuthContextProvider        # JWT token, login/logout, Cognito challenge handling
      > UserContextProvider      # Full user profile from /api/users/me
        > RBACContextProvider    # Role-based permissions (isSuperAdmin, orgRole, hasPermission)
          > OrganizationContextProvider  # Current org, members, invitations
            > ProjectContextProvider     # Projects and clients list
              > TimeTrackingContextProvider  # Active timer, today's entries, timer tick interval
```

Each context exposes a custom hook:

| Hook | Key Values / Methods |
|------|---------------------|
| `useAuth()` | `isAuthenticated`, `token`, `login()`, `logout()`, `setAuthData()` |
| `useUser()` | `user`, `updateProfile()`, `refreshUser()` |
| `useRBAC()` | `isSuperAdmin`, `orgRole`, `hasPermission()`, `canManageProjects`, `canApproveTimesheets` |
| `useThemeConfig()` | `config`, `updateConfig()` |
| `useNotification()` | `showSuccess()`, `showError()`, `showInfo()`, `showWarning()` |
| `useOrganization()` | `org`, `members`, `invitations`, `sendInvitation()`, `revokeInvitation()` |
| `useProject()` | `projects`, `clients`, `refreshProjects()` |
| `useTimeTracking()` | `activeTimer`, `startTimer()`, `stopTimer()`, `recentEntries`, `elapsedSeconds` |

### API Service Layer

All API calls go through `src/utils/api.service.ts` -- a singleton class wrapping Axios with ~106 methods.

**Request interceptor:**
- Reads `authToken` from localStorage, sets `Authorization: Bearer <token>`
- Reads `currentOrgId` from localStorage, sets `X-Org-Id` header

**Response interceptor:**
- On 401: clears auth state, redirects to `/login`

**Methods by category:**

| Category | Count | Examples |
|----------|-------|---------|
| Auth | 10 | `login()`, `register()`, `acceptInvitation()`, `oauthCallback()` |
| Users | 7 | `getCurrentUser()`, `updateUser()`, `updateUserRole()` |
| Organizations | 10 | `getCurrentOrg()`, `listOrgMembers()`, `createOrgInvitation()` |
| Projects | 9 | `listProjects()`, `createProject()`, `listProjectTasks()` |
| Clients | 6 | `listClients()`, `createClient()`, `getClientProjects()` |
| Time Entries | 15 | `startTimer()`, `stopTimer()`, `getDayEntries()`, `getWeekEntries()` |
| Timesheets | 7 | `submitTimesheet()`, `approveTimesheet()`, `rejectTimesheet()` |
| Reports | 7 | `getReportSummary()`, `getReportByProject()`, `exportReport()` |
| Dashboard | 3 | `getPersonalDashboard()`, `getTeamDashboard()`, `getOrgDashboard()` |
| AI Chat | 10 | `listChatSessions()`, `sendChatMessage()`, `listAIModels()` |
| Billing | 4 | `getPlans()`, `createCheckout()`, `createBillingPortal()` |
| Notifications | 4 | `listNotifications()`, `markNotificationRead()` |
| Super Admin | 5 | `superAdminListOrgs()`, `superAdminListUsers()`, `superAdminGetStats()` |
| Config | 4 | `getThemeConfig()`, `saveSettings()` |

---

## Routing

React Router v6 with `<ProtectedRoute>` wrapper and `<SmartRedirect>` for role-based defaults.

### Public Routes (inside `<PublicLayout>`)

| Path | Page | Description |
|------|------|-------------|
| `/` | HomePage | Landing page |
| `/pricing` | PricingPage | Billing plans |
| `/login` | LoginPage | Email/password + OAuth buttons |
| `/register` | RegisterPage | New user registration |
| `/forgot-password` | ForgotPasswordPage | Request password reset |
| `/reset-password/:token` | ResetPasswordPage | Reset with code |
| `/force-reset-password` | ForceResetPasswordPage | Cognito NEW_PASSWORD_REQUIRED |

### Standalone Public Routes

| Path | Page |
|------|------|
| `/auth/callback/:provider` | OAuthCallbackPage |
| `/accept-invitation/:token` | AcceptInvitationPage |
| `/verify-email` | VerifyEmailPage |

### Protected Routes (inside `<AppLayout>`, requires auth)

| Path | Page | Description |
|------|------|-------------|
| `/time` | TimeEntryPage | Timer + manual entry + day/week/month calendar |
| `/timesheet` | TimesheetPage | Weekly timesheet grid, submit for approval |
| `/projects` | ProjectsPage | Project list with search/filter |
| `/projects/:id` | ProjectDetailPage | Project details, tasks, budget, team |
| `/clients` | ClientsPage | Client management |
| `/dashboard` | DashboardPage | Personal/team/org stats and charts |
| `/reports` | ReportsPage | Reports with filters, CSV/PDF export |
| `/org/team` | TeamManagementPage | Invite members, manage roles, remove |
| `/org/settings` | OrgSettingsPage | Organization name, billing |
| `/settings` | PersonalSettingsPage | User profile, preferences |
| `/admin` | GlobalAdminPage | Super admin: all orgs and users |
| `/admin/settings` | SettingsPage | System settings: theme, chatbot, AI models |

### Setup Route

| Path | Page |
|------|------|
| `/setup` | OrgSetupWizard (multi-step org creation for new users) |

### SmartRedirect (catch-all `*`)

- Not authenticated -> `/login`
- Super admin -> `/admin`
- Has org -> `/time`

---

## Shared Components

| Component | File | Description |
|-----------|------|-------------|
| **AppLayout** | `shared/AppLayout.tsx` | Main app shell: sidebar nav, top bar with timer/AI/notifications/profile |
| **PublicLayout** | `shared/PublicLayout.tsx` | Public page wrapper with header |
| **PublicHeader** | `shared/PublicHeader.tsx` | Nav bar for unauthenticated pages |
| **AppHeader** | `shared/AppHeader.tsx` | Header for authenticated pages |
| **AppFooter** | `shared/AppFooter.tsx` | Footer with branding |
| **ProtectedRoute** | `shared/ProtectedRoute.tsx` | Auth guard with role checks (`adminOnly`, `superAdminOnly`, `minOrgRole`) |
| **LoadingSpinner** | `shared/LoadingSpinner.tsx` | Centered spinner with optional message |
| **TimerWidget** | `shared/TimerWidget.tsx` | Active timer in the top bar (start/stop/elapsed) |
| **AIChatDrawer** | `shared/AIChatDrawer.tsx` | AI assistant slide-out panel |
| **ChatPanel** | `shared/ChatPanel.tsx` | Chat UI inside the AI drawer |

### AppLayout sidebar navigation

**Organization users:** Track, Timesheet, Projects, Clients, Dashboard, Reports, Team

**Super admins:** Admin, System Settings

**Bottom nav:** Org Settings, Personal Settings

---

## Theme & Styling

- **MUI 5** dark theme defined in `src/theme/theme.ts`
- **Default colors:** primary `#7b6df6` (purple), secondary `#10b981` (green), background `#0a1628`
- **Tailwind CSS** for utility classes alongside MUI
- **Runtime-configurable** -- admin can change primary/secondary colors via ThemeConfig
- Component overrides: rounded buttons (10px), rounded cards (16px), custom table styling
- Font: Inter, Roboto, Helvetica, Arial

---

## Types

All TypeScript types are in `src/types/index.ts` (~425 lines).

### Key types

| Type | Description |
|------|-------------|
| `User` | Full user profile with roles, preferences, OAuth providers |
| `Organization` | Org settings, plan tier, Stripe fields |
| `Project` | Billable rates, budget, tags, parent/child hierarchy |
| `Client` | Contact info, billing entity |
| `TimeEntry` | Duration, timer state, approval status, narrative |
| `TimesheetWeek` | Weekly aggregation with submit/approve workflow |
| `DashboardStats` | Personal and org-level metrics |
| `AIChatSession` / `AIChatMessage` | Chat state |
| `AIModelConfig` | AI model with provider, config, active status |
| `ThemeConfig` | Colors, logo, app name |

### Role types

| Type | Values |
|------|--------|
| `OrgRole` | `'owner' \| 'admin' \| 'manager' \| 'member'` |
| `GlobalRole` | `'global_admin' \| 'user'` |
| `ProjectStatus` | `'active' \| 'archived' \| 'completed'` |
| `ApprovalStatus` | `'unsubmitted' \| 'pending' \| 'approved' \| 'rejected'` |
| `TimesheetStatus` | `'draft' \| 'submitted' \| 'approved' \| 'rejected'` |

### Constants

- `ORG_ROLE_HIERARCHY` -- member < manager < admin < owner
- `ORG_ROLE_PERMISSIONS` -- per-role capability matrix
- `ApiResponse<T>` / `PaginatedResponse<T>` -- API envelope types

---

## Hooks

| Hook | File | Description |
|------|------|-------------|
| `useBrowserTitle` | `hooks/useBrowserTitle.ts` | Updates the browser tab title with elapsed timer time (HH:MM:SS) |

---

## Key Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| React | 18.3 | UI framework |
| React Router | 6.21 | Client-side routing |
| Material UI | 5.14 | Component library (dark theme) |
| Tailwind CSS | 3.4 | Utility-first CSS |
| Axios | 1.8 | HTTP client |
| TypeScript | 4.9 | Type safety |
| Recharts | 2.13 | Charts and graphs |
| date-fns | 4.1 | Date utilities |
| Framer Motion | 12.23 | Animations |
| jsPDF | 4.2 | PDF export |
| XLSX | 0.18 | Excel export |
| React Markdown | 10.1 | Markdown rendering (AI chat) |
| Stripe.js | -- | Billing integration |

---

## Project Structure

```
frontend/src/
  components/
    context_providers/              # 8 React Context providers
      AuthContext.tsx                #   JWT auth, login/logout
      UserContext.tsx                #   User profile from API
      RBACContext.tsx                #   Role-based permissions
      ThemeConfigContext.tsx         #   Dynamic theme colors
      NotificationContext.tsx        #   Toast notifications (Snackbar)
      OrganizationContext.tsx        #   Current org, members, invites
      ProjectContext.tsx             #   Projects and clients
      TimeTrackingContext.tsx        #   Active timer, entries, tick interval
      __tests__/                    #   Context unit tests
    pages/                          # 24 page components
      HomePage.tsx                  #   Landing page
      LoginPage.tsx                 #   Login with OAuth
      RegisterPage.tsx              #   Registration form
      AcceptInvitationPage.tsx      #   Accept org invite token
      OAuthCallbackPage.tsx         #   OAuth redirect handler
      ForgotPasswordPage.tsx        #   Password reset request
      ResetPasswordPage.tsx         #   Reset with code/token
      ForceResetPasswordPage.tsx    #   Cognito forced password change
      VerifyEmailPage.tsx           #   Email verification
      PricingPage.tsx               #   Billing plans
      OrgSetupWizard.tsx            #   Multi-step org creation
      TimeEntryPage.tsx             #   Main time tracking
      TimesheetPage.tsx             #   Weekly timesheet grid
      ProjectsPage.tsx              #   Project list
      ProjectDetailPage.tsx         #   Single project details
      ClientsPage.tsx               #   Client management
      DashboardPage.tsx             #   Stats and charts
      ReportsPage.tsx               #   Reports with export
      TeamPage.tsx                  #   Team overview
      TeamManagementPage.tsx        #   Invite, roles, remove members
      OrgSettingsPage.tsx           #   Organization settings
      PersonalSettingsPage.tsx      #   User preferences
      GlobalAdminPage.tsx           #   Super admin console
      SettingsPage.tsx              #   System settings (theme, AI, chatbot)
      UsersPage.tsx                 #   Admin user list
    shared/                         # 10 shared components
      AppLayout.tsx                 #   Main app shell (sidebar + top bar)
      PublicLayout.tsx              #   Public page wrapper
      PublicHeader.tsx              #   Public nav bar
      AppHeader.tsx                 #   Authenticated header
      AppFooter.tsx                 #   Footer
      ProtectedRoute.tsx            #   Auth guard with role checks
      LoadingSpinner.tsx            #   Loading indicator
      TimerWidget.tsx               #   Timer in top bar
      AIChatDrawer.tsx              #   AI chat slide-out
      ChatPanel.tsx                 #   Chat UI component
  hooks/
    useBrowserTitle.ts              # Browser tab title with timer elapsed
  utils/
    api.service.ts                  # Singleton Axios API (~106 methods)
  configs/
    api.config.ts                   # API_BASE_URL, timeout, endpoint defs
    cognito.config.ts               # Cognito region, pool ID, client ID
  types/
    index.ts                        # All TypeScript interfaces and types
  theme/
    theme.ts                        # MUI dark theme + component overrides
  __mocks__/
    api.service.ts                  # Mock API service for tests
  App.tsx                           # Root: context providers + router
  App.css                           # App styles
  index.tsx                         # Entry point
  index.css                        # Global CSS variables
  setupTests.ts                    # Test setup (jest-dom)
```

## Key Conventions

- Context providers live in `src/components/context_providers/`
- Page components live in `src/components/pages/`
- Shared/reusable components live in `src/components/shared/`
- All TypeScript types are in `src/types/index.ts`
- Frontend types use camelCase; backend `to_api_dict()` converts snake_case to camelCase
- `CI=true npm run build` treats warnings as errors -- always test before pushing
