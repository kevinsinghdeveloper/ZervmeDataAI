# Infrastructure -- Terraform on AWS

The infrastructure is defined as Terraform code in `terraform/aws/`. It provisions a complete serverless stack for the Zerve My Time application.

## Resources

| Resource | Service | Description |
|----------|---------|-------------|
| Frontend Hosting | S3 + CloudFront | Static SPA hosting with HTTPS, gzip, HTTP/2+3 |
| Backend API | API Gateway HTTP + Lambda | Flask app via apig-wsgi, `$default` catch-all route |
| Authentication | Cognito User Pool | Email/password auth, JWT tokens (RS256), OAuth flows |
| Database | DynamoDB (16 tables) | PAY_PER_REQUEST billing, point-in-time recovery |
| File Storage | S3 (uploads bucket) | AES-256 encryption, versioning, public access blocked |
| Logs | CloudWatch | API Gateway access logs (30d), Lambda logs (14d) |
| State | S3 | Terraform state in `s3://zerve-terraform-state` |

## Architecture Diagram

```
                 +-----------+
    Users ------>| CloudFront|------> S3 (React build)
                 +-----------+

                 +-------------+      +--------+      +----------+
    API calls -->| API Gateway |----->| Lambda |----->| DynamoDB |
                 | (HTTP)      |      | (Flask)|      | (16 tbls)|
                 +-------------+      +--------+      +----------+
                                          |
                                    +-----+------+
                                    |   Cognito  |
                                    | (JWT Auth) |
                                    +------------+
```

## Terraform Files

| File | Resources |
|------|-----------|
| `main.tf` | Provider config, S3 state backend, `aws_caller_identity` data |
| `variables.tf` | All configurable variables + locals |
| `auth.tf` | Cognito User Pool, App Client, Pool Domain, JWT Authorizer |
| `backend.tf` | 16 DynamoDB tables, S3 uploads bucket, Lambda function, IAM role/policy, API Gateway + integration |
| `frontend.tf` | S3 frontend bucket, CloudFront distribution, OAC, bucket policy, Route53 record |
| `outputs.tf` | API URL, CloudFront domain, Cognito IDs, bucket names, Lambda ARN |

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | `us-east-1` | AWS region |
| `aws_profile` | `null` | AWS CLI profile |
| `project_name` | `zerve` | Used in resource naming prefix |
| `environment` | `dev` | Environment: dev, staging, prod |
| `domain_name` | `""` | Custom domain for CloudFront (optional) |
| `certificate_arn` | `""` | ACM cert for custom domain (optional) |
| `lambda_memory_size` | `256` | Lambda memory in MB |
| `lambda_timeout` | `30` | Lambda timeout in seconds |
| `api_throttling_rate_limit` | `1000` | API Gateway rate limit |
| `api_throttling_burst_limit` | `500` | API Gateway burst limit |
| `stripe_secret_key` | `""` | Stripe API key (sensitive) |
| `stripe_webhook_secret` | `""` | Stripe webhook secret (sensitive) |
| `google_oauth_client_id` | `""` | Google OAuth client ID |
| `google_oauth_client_secret` | `""` | Google OAuth secret (sensitive) |
| `oauth_internal_secret` | `""` | Internal OAuth password secret (sensitive) |

## Deployment

### Prerequisites

- Terraform >= 1.5.0
- AWS CLI configured with appropriate credentials
- S3 bucket `zerve-terraform-state` created for state storage

### Deploy

```bash
cd infrastructure/terraform/aws

# Initialize
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan

# View outputs
terraform output
```

### Outputs

After applying, Terraform outputs:

| Output | Example |
|--------|---------|
| API URL | `https://abc123.execute-api.us-east-1.amazonaws.com/dev` |
| CloudFront Domain | `https://d1234abcde.cloudfront.net` |
| CloudFront Distribution ID | `E2C4SCSRVKQWQE` |
| Cognito User Pool ID | `us-east-1_R7LaDuCWI` |
| Cognito Client ID | `1259agca7ctc1fbuglifa6tr1i` |
| Frontend S3 Bucket | `zerve-dev-frontend-396326422827` |
| Uploads S3 Bucket | `zerve-dev-uploads-396326422827` |
| Lambda Function Name | `zerve-dev-api` |

These values must be set as GitHub Actions secrets for CI/CD deployment.

## DynamoDB Tables (16)

Provisioned in `backend.tf`. All use PAY_PER_REQUEST billing.

### Core Tables (3)
- **users** -- PK: `id` | GSIs: EmailIndex, StatusIndex, OrgIdIndex
- **config** -- PK: `pk`, SK: `sk` | Key-value config store
- **audit_log** -- PK: `id`, SK: `timestamp` | GSIs: UserIdIndex, OrgIdIndex | TTL enabled

### Organization Tables (2)
- **organizations** -- PK: `id` | GSIs: SlugIndex, OwnerIdIndex, StripeCustomerIndex
- **org_invitations** -- PK: `id` | GSIs: OrgIdIndex, EmailIndex, TokenIndex | TTL enabled

### Business Tables (4)
- **clients** -- PK: `org_id`, SK: `id` | GSI: NameIndex
- **projects** -- PK: `org_id`, SK: `id` | GSIs: CodeIndex, ClientIdIndex, StatusIndex, ParentIndex
- **tasks** -- PK: `org_id`, SK: `id` | GSI: ProjectIdIndex
- **time_entries** -- PK: `org_id`, SK: `id` | GSIs: UserDateIndex, ProjectDateIndex, ClientDateIndex, ApprovalIndex, RunningTimerIndex

### Workflow Tables (3)
- **preset_narratives** -- PK: `org_id`, SK: `id` | GSIs: UserIdIndex, ProjectIdIndex
- **timesheets** -- PK: `org_id`, SK: `user_week` | GSIs: UserIdIndex, StatusIndex
- **notifications** -- PK: `user_id`, SK: `timestamp_id` | GSI: OrgIdIndex | TTL enabled

### AI Tables (2)
- **ai_chat_sessions** -- PK: `user_id`, SK: `id` | GSI: OrgIdIndex
- **ai_chat_messages** -- PK: `session_id`, SK: `timestamp_id`

### Billing & Integration Tables (2)
- **subscription_plans** -- PK: `id`
- **integrations** -- PK: `org_id`, SK: `provider_id` (future: Jira, GitHub, Slack)

## Security

- All S3 buckets: public access blocked, AES-256 encryption, versioning enabled
- Lambda IAM role: least-privilege (DynamoDB, S3, Cognito, Secrets Manager only)
- API Gateway: CORS configured, throttling enabled
- Cognito: password policy (8+ chars, uppercase + lowercase + number), email verification
- CloudFront: HTTPS redirect, TLS 1.2+
- Point-in-time recovery: enabled on all core tables, conditional on prod for others

## CI/CD Integration

The GitHub Actions workflow deploys code to the infrastructure provisioned by Terraform:

1. **Backend** -- Python code packaged as zip, uploaded to S3, deployed to Lambda via `update-function-code`
2. **Frontend** -- React build synced to S3, CloudFront cache invalidated

Required GitHub Actions secrets:
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `API_URL`, `LAMBDA_FUNCTION_NAME`
- `FRONTEND_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`
- `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`
