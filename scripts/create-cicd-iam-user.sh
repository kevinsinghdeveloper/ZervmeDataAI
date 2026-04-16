#!/bin/bash
set -euo pipefail

# Create IAM user with permanent access keys for GitHub Actions CI/CD
# Usage: ./create-cicd-iam-user.sh [environment] [aws-profile]

ENVIRONMENT="${1:-dev}"
AWS_PROFILE="${2:-default}"
PROJECT_NAME="zerve-dataai"
RESOURCE_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"
IAM_USER_NAME="${RESOURCE_PREFIX}-cicd"
POLICY_NAME="${RESOURCE_PREFIX}-cicd-deploy"
REGION="us-east-1"

echo "=== Create CI/CD IAM User ==="
echo "User:        $IAM_USER_NAME"
echo "Policy:      $POLICY_NAME"
echo "Environment: $ENVIRONMENT"
echo "Profile:     $AWS_PROFILE"
echo ""

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query "Account" --output text)
echo "AWS Account: $ACCOUNT_ID"
echo ""

# --- 1. Create IAM User ---
echo "Creating IAM user: $IAM_USER_NAME ..."
aws iam create-user \
  --user-name "$IAM_USER_NAME" \
  --tags Key=Project,Value="$PROJECT_NAME" Key=Environment,Value="$ENVIRONMENT" Key=ManagedBy,Value=script \
  --profile "$AWS_PROFILE" 2>/dev/null || echo "  (user already exists, continuing)"

# --- 2. Create and attach policy ---
# Minimum permissions for the CI/CD pipeline:
#   - S3: sync frontend, upload backend zip
#   - Lambda: update function code, wait for update
#   - CloudFront: create invalidation, get distribution
POLICY_DOC=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3DeployAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::${RESOURCE_PREFIX}-frontend-${ACCOUNT_ID}",
        "arn:aws:s3:::${RESOURCE_PREFIX}-frontend-${ACCOUNT_ID}/*"
      ]
    },
    {
      "Sid": "LambdaDeploy",
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration"
      ],
      "Resource": "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${RESOURCE_PREFIX}-api"
    },
    {
      "Sid": "CloudFrontInvalidation",
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetDistribution",
        "cloudfront:GetInvalidation"
      ],
      "Resource": "arn:aws:cloudfront::${ACCOUNT_ID}:distribution/*"
    }
  ]
}
EOF
)

echo "Attaching inline policy: $POLICY_NAME ..."
aws iam put-user-policy \
  --user-name "$IAM_USER_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document "$POLICY_DOC" \
  --profile "$AWS_PROFILE"

# --- 3. Create access keys ---
echo "Creating access keys ..."
KEYS=$(aws iam create-access-key \
  --user-name "$IAM_USER_NAME" \
  --profile "$AWS_PROFILE" \
  --output json)

ACCESS_KEY_ID=$(echo "$KEYS" | python3 -c "import sys,json; print(json.load(sys.stdin)['AccessKey']['AccessKeyId'])")
SECRET_ACCESS_KEY=$(echo "$KEYS" | python3 -c "import sys,json; print(json.load(sys.stdin)['AccessKey']['SecretAccessKey'])")

echo ""
echo "==========================================="
echo "  CI/CD IAM User Created Successfully"
echo "==========================================="
echo ""
echo "Set these as GitHub repository secrets:"
echo ""
echo "  AWS_ACCESS_KEY_ID      = $ACCESS_KEY_ID"
echo "  AWS_SECRET_ACCESS_KEY  = $SECRET_ACCESS_KEY"
echo ""
echo "You can set them with the gh CLI:"
echo ""
echo "  gh secret set AWS_ACCESS_KEY_ID --body \"$ACCESS_KEY_ID\""
echo "  gh secret set AWS_SECRET_ACCESS_KEY --body \"$SECRET_ACCESS_KEY\""
echo ""
echo "IMPORTANT: Save these keys now — the secret key cannot be retrieved again."
echo ""