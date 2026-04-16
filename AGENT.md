# Agent Instructions - Zerve App

## Overview

This document provides instructions for AI agents working on the Zerve App codebase. Follow these conventions strictly when making changes.

## Decision Framework

### Before Adding a Feature
1. Check if a similar feature exists in the consulting-react-template patterns
2. Follow the established 4-layer architecture (Controller -> Manager -> Service -> DB)
3. Add audit logging for any user-facing action
4. Ensure RBAC permissions are checked where appropriate

### Before Modifying Code
1. Read the existing file first
2. Follow the patterns already established in that layer
3. Do not introduce new dependencies without justification
4. Keep the separation of concerns between layers

## Frontend Workflow

### Adding a New Page
1. Create the page component in `frontend/src/components/pages/NewPage.tsx`
2. Add the route in `frontend/src/App.tsx`
3. If protected, wrap with `<ProtectedRoute>` (add `adminOnly` if needed)
4. Add navigation link in `frontend/src/components/shared/AppHeader.tsx`
5. Add any new types to `frontend/src/types/index.ts`

### Adding a New Context Provider
1. Create in `frontend/src/components/context_providers/NewContext.tsx`
2. Export a `useNewContext()` hook
3. Wrap in `App.tsx` inside the provider tree (order matters for dependencies)
4. Follow the pattern: state + loading + error + fetch + CRUD methods

### Adding an API Method
1. Add the endpoint to `frontend/src/configs/api.config.ts`
2. Add the method to `frontend/src/utils/api.service.ts`
3. Call from the appropriate context provider or page component

## Backend Workflow

### Adding a New API Endpoint
1. Create the controller in `backend/controllers/<domain>/<Domain>Controller.py`
   - Extend `IController`
   - Implement `register_all_routes()` and route handlers
   - Parse request, create `RequestResourceModel`, call manager
2. Create the manager in `backend/managers/<domain>/<Domain>ResourceManager.py`
   - Extend `IResourceManager`
   - Implement business logic in `get()`, `post()`, `put()`, `delete()`
   - Use `SessionLocal()` for DB access, always close in `finally`
3. Register in `backend/run_web_service.py`:
   - Import controller and manager
   - Instantiate manager with service dependencies
   - Call `register_controller(app, Controller, manager)`

### Adding a Database Model
1. Create in `backend/database/models/NewModel.py`
   - Extend `Base` from `database.db`
   - Add `to_dict()` method for serialization
   - Use UUID primary keys
   - Add `created_at` and `updated_at` timestamps
2. Import in `backend/database/db.py` inside `init_db()`

### Adding a Service
1. Create in `backend/services/<category>/<ServiceName>.py`
   - Extend `IServiceManagerBase`
   - Implement `initialize()` for setup
   - Add service-specific methods
2. Inject into managers via the `service_managers` dict

## Security Checklist

- [ ] All protected endpoints use `@token_required` decorator
- [ ] Admin-only endpoints verify `user.is_admin` or `user.role == 'admin'`
- [ ] File uploads validate file type and size
- [ ] SQL queries use SQLAlchemy ORM (no raw SQL)
- [ ] API keys are encrypted with Fernet before storage
- [ ] Destructive actions are audit-logged
- [ ] CORS is configured for specific origins in production
- [ ] No secrets hardcoded in code

## Infrastructure Workflow

### Modifying AWS Resources
1. Edit the appropriate `.tf` file in `infrastructure/terraform/aws/`
2. Run `terraform plan` to preview changes
3. Review the plan carefully before applying
4. Update `outputs.tf` if new outputs are needed

### Deploying
- **Local dev**: `docker-compose up --build`
- **AWS**: `./scripts/deploy-terraform-aws.sh <env> <profile> <region>`
- **CI/CD**: Push to `main` branch triggers GitHub Actions

## Testing Requirements

### Frontend
- Unit tests for context providers and utility functions
- Component tests for pages with user interactions
- E2E tests for critical flows (login, dashboard, chat)

### Backend
- Unit tests for managers (business logic)
- Integration tests for controllers (API endpoints)
- Service tests with mocked external dependencies

## Common Patterns

### Error Handling (Frontend)
```tsx
try {
  await apiService.someMethod();
  showSuccess('Action completed');
} catch (err: any) {
  showError(err.message || 'Something went wrong');
}
```

### Error Handling (Backend)
```python
db = SessionLocal()
try:
    # ... business logic
    db.commit()
    return ResponseModel(success=True, data=result)
except Exception as e:
    db.rollback()
    return ResponseModel(success=False, error=str(e), status_code=500)
finally:
    db.close()
```

### Audit Logging
```python
audit = AuditLog(
    user_id=str(user_id),
    action="resource_created",
    resource="resource_name",
    details={"key": "value"},
)
db.add(audit)
```
