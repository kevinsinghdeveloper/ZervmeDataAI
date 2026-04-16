# Plan: Migrate Zerve App to Use AWS Resources

## Context

Terraform provisioned 24 AWS resources (Cognito, DynamoDB, S3, API Gateway, CloudFront) but the app uses **none of them** — it runs on PostgreSQL, local filesystem, custom JWT, and Flask dev server. This plan rewrites the app to fully utilize the provisioned AWS infrastructure and ensures GitHub Actions deploys correctly to these resources.

---

## Phase 1: Lambda + API Gateway (Foundation)

**Goal:** Get Flask running on Lambda behind the existing API Gateway.

### 1.1 Add Lambda function to Terraform
**File:** `infrastructure/terraform/aws/backend.tf`
- Add `aws_lambda_function.api` (Python 3.12, handler = `handler.handler`)
- Add `aws_apigatewayv2_integration.lambda` (AWS_PROXY to Lambda)
- Add `aws_apigatewayv2_route.default` (`$default` catch-all route)
- Add `aws_lambda_permission.api_gateway`
- Add `aws_cloudwatch_log_group.lambda`
- Lambda env vars: `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `UPLOADS_BUCKET`, `DYNAMODB_TABLE_PREFIX`, `AWS_REGION_NAME`
- Use `lifecycle { ignore_changes = [filename, source_code_hash] }` so CI/CD manages code

### 1.2 Add Lambda outputs to Terraform
**File:** `infrastructure/terraform/aws/outputs.tf`
- Add `lambda_function_name` and `lambda_function_arn` outputs

### 1.3 Create Lambda entry point
**File (NEW):** `backend/handler.py`
- Use Mangum to wrap Flask WSGI app: `handler = Mangum(create_app(), lifespan="off")`

### 1.4 Add mangum dependency
**File:** `backend/requirements.txt`
- Add `mangum==0.17.0`

### 1.5 Verify
- `terraform apply` → Lambda + API Gateway integration created
- `curl https://5uqatq8et1.execute-api.us-east-1.amazonaws.com/dev/api/health` → 200

---

## Phase 2: DynamoDB Tables + Database Layer

**Goal:** Replace PostgreSQL/SQLAlchemy with DynamoDB for all data storage.

### 2.1 Add 7 missing DynamoDB tables to Terraform
**File:** `infrastructure/terraform/aws/backend.tf`
- `users` table (PK: `id`, GSI: `EmailIndex` on `email`)
- `documents` table (PK: `id`, GSI: `UserIdIndex` on `userId` + `createdAt`)
- `document-chunks` table (PK: `documentId`, SK: `chunkIndex`)
- `models` table (PK: `id`, GSI: `UserIdIndex` on `userId`)
- `pipelines` table (PK: `id`, GSI: `UserIdIndex` on `userId`)
- `queries` table (PK: `id`, GSI: `UserIdIndex` on `userId`+`createdAt`, GSI: `PipelineIdIndex` on `pipelineId`+`createdAt`)
- `subscription-plans` table (PK: `id`)
- Update Lambda IAM policy to include all new table ARNs + index ARNs

### 2.2 Create DynamoDB client module
**File (NEW):** `backend/database/dynamodb.py`
- Singleton `boto3.resource('dynamodb')` with `get_table(logical_name)` helper
- Table name mapping: logical name → `{DYNAMODB_TABLE_PREFIX}-{suffix}`
- Support `DYNAMODB_ENDPOINT_URL` env var for local DynamoDB
- `init_db()` function that verifies connectivity

### 2.3 Create DynamoDB item schemas
**Dir (NEW):** `backend/database/schemas/`
- `user.py` — UserItem dataclass with `to_item()`, `to_api_dict()`, `from_item()`
- `document.py` — DocumentItem
- `document_chunk.py` — DocumentChunkItem (embeddings stored as JSON-serialized float list)
- `query.py` — QueryItem
- `audit_log.py` — AuditLogItem
- `model.py` — ModelItem
- `pipeline.py` — PipelineItem
- `subscription_plan.py` — SubscriptionPlanItem

### 2.4 Replace `database/db.py`
**File:** `backend/database/db.py`
- Remove SQLAlchemy engine, SessionLocal, Base
- Re-export `init_db` and `get_table` from `database/dynamodb.py`

### 2.5 Rewrite all managers for DynamoDB
Replace every `SessionLocal()` + `db.query()` with `get_table()` + boto3 operations:

**File:** `backend/managers/auth/AuthResourceManager.py`
- Email lookup → GSI query on `EmailIndex`
- User insert → `table.put_item()`
- Audit log insert → `audit_table.put_item()`

**File:** `backend/managers/users/UserResourceManager.py`
- User by ID → `table.get_item(Key={"id": ...})`
- List users → `table.scan()` with pagination via `LastEvaluatedKey`
- Update user → `table.update_item()` with UpdateExpression
- Delete user → cascade delete (documents, chunks, pipelines, queries) then `table.delete_item()`

**File:** `backend/managers/documents/DocumentResourceManager.py`
- List by user → GSI query on `UserIdIndex`
- Get by ID + user → `table.get_item()` + verify userId matches

**File:** `backend/managers/chat/ChatResourceManager.py`
- Chat history → GSI query on `UserIdIndex`, sorted by `createdAt`
- Save query → `table.put_item()`

**File:** `backend/managers/config/ConfigResourceManager.py`
- Theme/settings → DynamoDB config table with `pk="CONFIG"`, `sk="theme"|"settings"`
- Replace JSON file read/write with `table.get_item()`/`table.put_item()`

**File:** `backend/managers/audit/AuditResourceManager.py`
- List logs → `table.scan()` with FilterExpression for action/userId/timestamp

### 2.6 Update `run_web_service.py`
**File:** `backend/run_web_service.py`
- Replace `from database.db import init_db` (now calls DynamoDB connectivity check)
- Remove PostgreSQL-specific error messaging

### 2.7 Verify
- `terraform apply` → 7 new tables created
- Deploy to Lambda → health check passes
- PUT item manually in users table → `/api/users/me` returns it

---

## Phase 3: S3 Storage

**Goal:** Replace local filesystem with S3 for document uploads.

### 3.1 Create S3StorageService
**File (NEW):** `backend/services/storage/S3StorageService.py`
- Implements `IStorageManager` interface (same as `LocalStorageService`)
- Uses `boto3.client('s3')` for `upload_file`, `download_file`, `delete_file`, `file_exists`, `list_files`, `get_file_size`
- S3 key pattern: `{user_id}/{uuid}.{ext}`

### 3.2 Update storage initialization
**File:** `backend/run_web_service.py`
- If `UPLOADS_BUCKET` env var is set → use `S3StorageService(bucket_name=...)`
- Else → fall back to `LocalStorageService` for local dev

### 3.3 Update DocumentResourceManager for S3
**File:** `backend/managers/documents/DocumentResourceManager.py`
- `_upload_document`: Read file bytes, upload to S3 via storage service, store S3 key as `file_path`
- `_delete_document`: Delete from S3 via storage service instead of `os.remove()`

### 3.4 Update DocumentProcessorService for S3
**File:** `backend/services/processing/DocumentProcessorService.py`
- Download file from S3 to `/tmp` (Lambda has 512MB tmp space)
- Extract text from tmp file
- Clean up tmp after processing

### 3.5 Verify
- Upload document via API → file appears in `zerve-dev-uploads-396326422827` S3 bucket
- Delete document → removed from S3 and DynamoDB

---

## Phase 4: Cognito Authentication

**Goal:** Replace custom JWT/bcrypt with AWS Cognito.

### 4.1 Rewrite backend auth_utils for Cognito JWT
**File:** `backend/utils/auth_utils.py`
- Remove `create_access_token`, `create_refresh_token`, `hash_password`, `verify_password`
- Add `decode_cognito_token()` — fetches JWKS from Cognito, validates RS256 JWT
- Cache JWKS keys for 1 hour
- `@token_required` now extracts `sub` and `email` from Cognito token claims
- `request.user_id` = Cognito `sub` (UUID)

### 4.2 Rewrite AuthResourceManager for Cognito SDK
**File:** `backend/managers/auth/AuthResourceManager.py`
- `_register()` → `cognito_client.sign_up()` + create user profile in DynamoDB
- `_login()` → `cognito_client.initiate_auth(AuthFlow='USER_PASSWORD_AUTH')` → returns Cognito tokens
- `_refresh()` → `cognito_client.initiate_auth(AuthFlow='REFRESH_TOKEN_AUTH')`
- `_verify_email()` → `cognito_client.confirm_sign_up()`
- `_forgot_password()` → `cognito_client.forgot_password()`
- `_reset_password()` → `cognito_client.confirm_forgot_password()`
- First-user auto-admin: check DynamoDB users table count, if 0 → set role=admin

### 4.3 Add Cognito config to frontend
**File:** `frontend/package.json` — Add `amazon-cognito-identity-js: ^6.3.0`

**File (NEW):** `frontend/src/configs/cognito.config.ts`
- Export `COGNITO_CONFIG` with `USER_POOL_ID`, `CLIENT_ID`, `REGION` from env vars

### 4.4 Update frontend AuthContext for Cognito
**File:** `frontend/src/components/context_providers/AuthContext.tsx`
- `login()` → Backend still proxies to Cognito via `/api/auth/login`, returns tokens
- Store Cognito `accessToken` (or `idToken`) as `authToken` in localStorage
- Token expiration check still works (Cognito tokens are standard JWTs)
- Keep the same AuthContext interface so no downstream component changes needed

### 4.5 Remove auth-related fields from User schema
**File:** `backend/database/schemas/user.py`
- Remove: `hashed_password`, `verification_token`, `reset_token`, `reset_token_expires`
- Keep: `id` (= Cognito sub), `email`, `role`, `is_admin`, `is_active`, etc.

### 4.6 Update Cognito callback URLs in Terraform
**File:** `infrastructure/terraform/aws/auth.tf`
- Add CloudFront domain to `callback_urls` and `logout_urls`

### 4.7 Verify
- Register → user created in Cognito + DynamoDB
- Login → Cognito tokens returned
- Authenticated API call → `@token_required` validates Cognito JWT
- Password reset flow works via Cognito

---

## Phase 5: GitHub Actions CI/CD

**Goal:** Deploy backend to Lambda + frontend to S3/CloudFront correctly.

### 5.1 Update deploy-aws.yml backend job
**File:** `.github/workflows/deploy-aws.yml`
- Package: `zip` includes `handler.py` (Lambda entry point)
- Deploy: `aws lambda update-function-code --function-name ${{ secrets.LAMBDA_FUNCTION_NAME }} --zip-file fileb://backend.zip --publish`
- Wait: `aws lambda wait function-updated-v2`
- Smoke test: `curl` the health endpoint, fail if not 200

### 5.2 Update deploy-aws.yml frontend job
**File:** `.github/workflows/deploy-aws.yml`
- Add Cognito env vars to the build step:
  - `REACT_APP_COGNITO_USER_POOL_ID: ${{ secrets.COGNITO_USER_POOL_ID }}`
  - `REACT_APP_COGNITO_CLIENT_ID: ${{ secrets.COGNITO_CLIENT_ID }}`
  - `REACT_APP_COGNITO_REGION: us-east-1`

### 5.3 Required GitHub Secrets
| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `LAMBDA_FUNCTION_NAME` | `zerve-dev-api` |
| `API_URL` | `https://5uqatq8et1.execute-api.us-east-1.amazonaws.com/dev` |
| `FRONTEND_BUCKET` | `zerve-dev-frontend-396326422827` |
| `CLOUDFRONT_DISTRIBUTION_ID` | `E26I6H46CU4EEM` |
| `COGNITO_USER_POOL_ID` | `us-east-1_CgULCtP07` |
| `COGNITO_CLIENT_ID` | `5jdjpoc68buppvl1jde90egcc` |

### 5.4 Verify
- Push to `main` → CI passes → deploy triggers
- Backend Lambda code updated → health check passes
- Frontend deployed to S3 → CloudFront cache invalidated
- End-to-end: register, login, upload doc, chat, view audit logs

---

## Phase 6: Cleanup

### 6.1 Remove dead dependencies from `backend/requirements.txt`
- Remove: `SQLAlchemy`, `psycopg2-binary`, `pgvector`, `alembic`

### 6.2 Remove old database models
- Remove or archive `backend/database/models/` (SQLAlchemy models replaced by `database/schemas/`)

### 6.3 Update `.env.example`
- Remove: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES`, `JWT_REFRESH_TOKEN_EXPIRES`
- Add: `AWS_REGION_NAME`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `UPLOADS_BUCKET`, `DYNAMODB_TABLE_PREFIX`
- Add frontend vars: `REACT_APP_COGNITO_*`

### 6.4 Update `docker-compose.yml`
- Replace PostgreSQL service with `amazon/dynamodb-local` for local dev
- Update backend env vars for AWS services
- Remove `postgres_data` volume

---

## Files Summary

| Phase | Files Modified | Files Created |
|-------|---------------|---------------|
| 1 | `backend.tf`, `outputs.tf`, `requirements.txt` | `backend/handler.py` |
| 2 | `backend.tf` (IAM + tables), `db.py`, all 6 managers, `run_web_service.py` | `database/dynamodb.py`, `database/schemas/*.py` (8 files) |
| 3 | `run_web_service.py`, `DocumentResourceManager.py`, `DocumentProcessorService.py` | `services/storage/S3StorageService.py` |
| 4 | `auth_utils.py`, `AuthResourceManager.py`, `AuthContext.tsx`, `auth.tf`, `package.json` | `configs/cognito.config.ts` |
| 5 | `deploy-aws.yml` | — |
| 6 | `requirements.txt`, `.env.example`, `docker-compose.yml` | — |

## Verification (End-to-End)

After all phases:
1. `terraform apply` → all resources provisioned
2. Push to `main` → CI passes, deploy runs, Lambda updated, frontend deployed
3. Visit CloudFront URL → homepage loads
4. Register → user in Cognito + DynamoDB users table
5. Login → Cognito tokens, redirected to dashboard
6. Upload document → file in S3, record in DynamoDB documents table
7. Chat → response from LLM, query saved in DynamoDB queries table
8. Admin panel → audit logs from DynamoDB audit-log table
9. Health check → `https://5uqatq8et1.execute-api.us-east-1.amazonaws.com/dev/api/health` returns 200
