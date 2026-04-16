#!/bin/bash
set -euo pipefail

# Zerve App - AWS Terraform Deployment Script
ENVIRONMENT="${1:-dev}"
AWS_PROFILE="${2:-default}"
REGION="${3:-us-east-1}"

echo "=== Zerve App AWS Deployment ==="
echo "Environment: $ENVIRONMENT"
echo "AWS Profile: $AWS_PROFILE"
echo "Region: $REGION"
echo ""

cd "$(dirname "$0")/../infrastructure/terraform/aws"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init \
  -backend-config="key=zerve/${ENVIRONMENT}/terraform.tfstate"

# Plan
echo "Planning infrastructure changes..."
terraform plan \
  -var="environment=${ENVIRONMENT}" \
  -var="aws_region=${REGION}" \
  -var="aws_profile=${AWS_PROFILE}" \
  -out=tfplan

# Apply
read -p "Apply changes? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  terraform apply tfplan
  echo ""
  echo "=== Deployment Complete ==="
  terraform output deployment_summary
fi
