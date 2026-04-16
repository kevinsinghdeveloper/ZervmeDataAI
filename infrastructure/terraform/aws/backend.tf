# Backend Infrastructure
# API Gateway + DynamoDB + Lambda Functions

# ============================================================
# DynamoDB Tables (21 total)
# ============================================================

# --- KEPT/MODIFIED Tables (3) ---

resource "aws_dynamodb_table" "config" {
  name         = "${local.resource_prefix}-config"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = { Name = "${local.resource_prefix}-config" }
}

resource "aws_dynamodb_table" "audit_log" {
  name         = "${local.resource_prefix}-audit-log"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "timestamp"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }
  attribute {
    name = "userId"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }

  global_secondary_index {
    name            = "UserIdIndex"
    hash_key        = "userId"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "OrgIdIndex"
    hash_key        = "org_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  tags = { Name = "${local.resource_prefix}-audit-log" }
}

resource "aws_dynamodb_table" "users" {
  name         = "${local.resource_prefix}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "EmailIndex"
    hash_key        = "email"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "OrgIdIndex"
    hash_key        = "org_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-users" })
}

# --- NEW Tables (13) ---

resource "aws_dynamodb_table" "organizations" {
  name         = "${local.resource_prefix}-organizations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "slug"
    type = "S"
  }
  attribute {
    name = "owner_id"
    type = "S"
  }
  global_secondary_index {
    name            = "SlugIndex"
    hash_key        = "slug"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "OwnerIdIndex"
    hash_key        = "owner_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-organizations" })
}

resource "aws_dynamodb_table" "org_invitations" {
  name         = "${local.resource_prefix}-org-invitations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "token"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "OrgIdIndex"
    hash_key        = "org_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "EmailIndex"
    hash_key        = "email"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "TokenIndex"
    hash_key        = "token"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at_ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-org-invitations" })
}

resource "aws_dynamodb_table" "projects" {
  name         = "${local.resource_prefix}-projects"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "org_id"
  range_key    = "id"

  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "org_id"
    range_key       = "status"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-projects" })
}

resource "aws_dynamodb_table" "notifications" {
  name         = "${local.resource_prefix}-notifications"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "timestamp_id"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "timestamp_id"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }

  global_secondary_index {
    name            = "OrgIdIndex"
    hash_key        = "org_id"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at_ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-notifications" })
}

resource "aws_dynamodb_table" "ai_chat_sessions" {
  name         = "${local.resource_prefix}-ai-chat-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "id"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }

  global_secondary_index {
    name            = "OrgIdIndex"
    hash_key        = "org_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-ai-chat-sessions" })
}

resource "aws_dynamodb_table" "ai_chat_messages" {
  name         = "${local.resource_prefix}-ai-chat-messages"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "timestamp_id"

  attribute {
    name = "session_id"
    type = "S"
  }
  attribute {
    name = "timestamp_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-ai-chat-messages" })
}

resource "aws_dynamodb_table" "user_roles" {
  name         = "${local.resource_prefix}-user-roles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "org_role"

  attribute {
    name = "user_id"
    type = "S"
  }
  attribute {
    name = "org_role"
    type = "S"
  }
  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "role"
    type = "S"
  }

  global_secondary_index {
    name            = "OrgMembersIndex"
    hash_key        = "org_id"
    range_key       = "role"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "RoleIndex"
    hash_key        = "role"
    range_key       = "user_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-user-roles" })
}

# --- AI / Reporting Tables (5) ---

resource "aws_dynamodb_table" "reports" {
  name         = "${local.resource_prefix}-reports"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "org_id"
  range_key    = "id"

  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "project_id"
    type = "S"
  }

  global_secondary_index {
    name            = "ProjectIdIndex"
    hash_key        = "project_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-reports" })
}

resource "aws_dynamodb_table" "report_jobs" {
  name         = "${local.resource_prefix}-report-jobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "org_id"
  range_key    = "id"

  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "report_id"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "ReportIdIndex"
    hash_key        = "report_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    range_key       = "org_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-report-jobs" })
}

resource "aws_dynamodb_table" "datasets" {
  name         = "${local.resource_prefix}-datasets"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "org_id"
  range_key    = "id"

  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-datasets" })
}

resource "aws_dynamodb_table" "model_configs" {
  name         = "${local.resource_prefix}-model-configs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "org_id"
  range_key    = "id"

  attribute {
    name = "org_id"
    type = "S"
  }
  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-model-configs" })
}

resource "aws_dynamodb_table" "report_cache" {
  name         = "${local.resource_prefix}-report-cache"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "report_id"
  range_key    = "cache_key"

  attribute {
    name = "report_id"
    type = "S"
  }
  attribute {
    name = "cache_key"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = false
  }

  tags = merge(local.common_tags, { Name = "${local.resource_prefix}-report-cache" })
}

# ============================================================
# S3 Bucket for uploads
# ============================================================

resource "aws_s3_bucket" "uploads" {
  bucket = "${local.resource_prefix}-uploads-${data.aws_caller_identity.current.account_id}"
  tags   = { Name = "${local.resource_prefix}-uploads" }
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================
# IAM Role for Lambda
# ============================================================

resource "aws_iam_role" "lambda_execution" {
  name = "${local.resource_prefix}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = { Name = "${local.resource_prefix}-lambda-execution-role" }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom" {
  name = "${local.resource_prefix}-lambda-custom-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:BatchGetItem", "dynamodb:BatchWriteItem", "dynamodb:DescribeTable"]
        Resource = [
          aws_dynamodb_table.config.arn, "${aws_dynamodb_table.config.arn}/index/*",
          aws_dynamodb_table.audit_log.arn, "${aws_dynamodb_table.audit_log.arn}/index/*",
          aws_dynamodb_table.users.arn, "${aws_dynamodb_table.users.arn}/index/*",
          aws_dynamodb_table.organizations.arn, "${aws_dynamodb_table.organizations.arn}/index/*",
          aws_dynamodb_table.org_invitations.arn, "${aws_dynamodb_table.org_invitations.arn}/index/*",
          aws_dynamodb_table.projects.arn, "${aws_dynamodb_table.projects.arn}/index/*",
          aws_dynamodb_table.notifications.arn, "${aws_dynamodb_table.notifications.arn}/index/*",
          aws_dynamodb_table.ai_chat_sessions.arn, "${aws_dynamodb_table.ai_chat_sessions.arn}/index/*",
          aws_dynamodb_table.ai_chat_messages.arn, "${aws_dynamodb_table.ai_chat_messages.arn}/index/*",
          aws_dynamodb_table.user_roles.arn, "${aws_dynamodb_table.user_roles.arn}/index/*",
          aws_dynamodb_table.reports.arn, "${aws_dynamodb_table.reports.arn}/index/*",
          aws_dynamodb_table.report_jobs.arn, "${aws_dynamodb_table.report_jobs.arn}/index/*",
          aws_dynamodb_table.datasets.arn, "${aws_dynamodb_table.datasets.arn}/index/*",
          aws_dynamodb_table.model_configs.arn, "${aws_dynamodb_table.model_configs.arn}/index/*",
          aws_dynamodb_table.report_cache.arn, "${aws_dynamodb_table.report_cache.arn}/index/*",
        ]
      },
      {
        Sid      = "S3Access"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [aws_s3_bucket.uploads.arn, "${aws_s3_bucket.uploads.arn}/*"]
      },
      {
        Sid      = "SecretsManagerAccess"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = ["arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${local.resource_prefix}*"]
      },
      {
        Sid    = "CognitoAccess"
        Effect = "Allow"
        Action = [
          "cognito-idp:SignUp",
          "cognito-idp:InitiateAuth",
          "cognito-idp:ConfirmSignUp",
          "cognito-idp:AdminConfirmSignUp",
          "cognito-idp:ForgotPassword",
          "cognito-idp:ConfirmForgotPassword",
          "cognito-idp:AdminGetUser",
          "cognito-idp:GlobalSignOut",
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminSetUserPassword",
          "cognito-idp:AdminUpdateUserAttributes",
          "cognito-idp:RespondToAuthChallenge"
        ]
        Resource = [aws_cognito_user_pool.main.arn]
      },
      {
        Sid      = "SESAccess"
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = ["*"]
      }
    ]
  })
}

# ============================================================
# Placeholder Lambda Package
# ============================================================

data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"

  source {
    content  = <<-EOF
      def handler(event, context):
          return {"statusCode": 200, "body": "Placeholder - deploy code via CI/CD"}
    EOF
    filename = "placeholder.py"
  }
}

# ============================================================
# API Gateway
# ============================================================

resource "aws_apigatewayv2_api" "main" {
  name          = "${local.resource_prefix}-api"
  protocol_type = "HTTP"
  description   = "API Gateway for ${var.project_name} ${var.environment}"

  cors_configuration {
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers     = ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Org-Id"]
    expose_headers    = ["*"]
    max_age           = 300
    allow_credentials = false
  }

  tags = { Name = "${local.resource_prefix}-api" }
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = var.api_throttling_rate_limit
    throttling_burst_limit = var.api_throttling_burst_limit
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
    })
  }

  tags = { Name = "${local.resource_prefix}-api-stage" }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.resource_prefix}-api"
  retention_in_days = 30
  tags              = { Name = "${local.resource_prefix}-api-logs" }
}

# ============================================================
# Lambda Function
# ============================================================

resource "aws_lambda_function" "api" {
  function_name    = "${local.resource_prefix}-api"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout

  environment {
    variables = {
      ENVIRONMENT           = var.environment
      AWS_REGION_NAME       = var.aws_region
      COGNITO_USER_POOL_ID  = aws_cognito_user_pool.main.id
      COGNITO_CLIENT_ID     = aws_cognito_user_pool_client.main.id
      UPLOADS_BUCKET        = aws_s3_bucket.uploads.id
      DYNAMODB_TABLE_PREFIX = local.resource_prefix
      CORS_ORIGINS          = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.frontend.domain_name}"
      API_STAGE             = var.environment
      GOOGLE_OAUTH_CLIENT_ID  = var.google_oauth_client_id
      GOOGLE_OAUTH_CLIENT_SECRET = var.google_oauth_client_secret
      GOOGLE_OAUTH_ENABLED    = var.google_oauth_client_id != "" ? "true" : "false"
      OAUTH_INTERNAL_SECRET   = var.oauth_internal_secret
      SES_FROM_EMAIL          = var.ses_from_email
    }
  }

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  tags = { Name = "${local.resource_prefix}-api" }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 14
  tags              = { Name = "${local.resource_prefix}-lambda-logs" }
}

# ============================================================
# API Gateway Lambda Integration
# ============================================================

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
