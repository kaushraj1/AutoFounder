#!/usr/bin/env bash
# Bootstrap the Terraform remote-state backend for an environment.
# Creates the versioned, encrypted, private S3 state bucket and the shared
# DynamoDB lock table. Idempotent — safe to re-run.
#
# Usage:  ./bootstrap-state.sh <staging|production> [region]
# Requires: awscli v2, credentials with S3 + DynamoDB create permissions.
set -euo pipefail

ENVIRONMENT="${1:-}"
REGION="${2:-ap-south-1}"
LOCK_TABLE="autofounder-ai-tfstate-lock"

if [[ "${ENVIRONMENT}" != "staging" && "${ENVIRONMENT}" != "production" ]]; then
  echo "Usage: $0 <staging|production> [region]" >&2
  exit 1
fi

BUCKET="autofounder-ai-tfstate-${ENVIRONMENT}"

echo "==> Region: ${REGION}  Bucket: ${BUCKET}  Lock table: ${LOCK_TABLE}"

# --- S3 state bucket -------------------------------------------------------
if aws s3api head-bucket --bucket "${BUCKET}" --region "${REGION}" 2>/dev/null; then
  echo "==> Bucket ${BUCKET} already exists."
else
  echo "==> Creating bucket ${BUCKET}..."
  if [[ "${REGION}" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}"
  else
    aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" \
      --create-bucket-configuration "LocationConstraint=${REGION}"
  fi
fi

echo "==> Enabling versioning, encryption, and public-access block..."
aws s3api put-bucket-versioning --bucket "${BUCKET}" \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption --bucket "${BUCKET}" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":true}]}'

aws s3api put-public-access-block --bucket "${BUCKET}" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws s3api put-bucket-lifecycle-configuration --bucket "${BUCKET}" \
  --lifecycle-configuration '{"Rules":[{"ID":"expire-noncurrent-state","Status":"Enabled","Filter":{"Prefix":""},"NoncurrentVersionExpiration":{"NoncurrentDays":90}}]}'

# Deny any non-TLS access to the state bucket (CIS S3.5). A Deny policy with
# Principal "*" does not grant public access, so it is allowed under the
# public-access-block above.
aws s3api put-bucket-policy --bucket "${BUCKET}" --policy "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{
    \"Sid\": \"DenyInsecureTransport\",
    \"Effect\": \"Deny\",
    \"Principal\": \"*\",
    \"Action\": \"s3:*\",
    \"Resource\": [\"arn:aws:s3:::${BUCKET}\", \"arn:aws:s3:::${BUCKET}/*\"],
    \"Condition\": {\"Bool\": {\"aws:SecureTransport\": \"false\"}}
  }]
}"

# --- DynamoDB lock table (shared across environments) ----------------------
if aws dynamodb describe-table --table-name "${LOCK_TABLE}" --region "${REGION}" >/dev/null 2>&1; then
  echo "==> Lock table ${LOCK_TABLE} already exists."
else
  echo "==> Creating DynamoDB lock table ${LOCK_TABLE}..."
  aws dynamodb create-table \
    --table-name "${LOCK_TABLE}" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --sse-specification Enabled=true,SSEType=KMS \
    --region "${REGION}"
  aws dynamodb wait table-exists --table-name "${LOCK_TABLE}" --region "${REGION}"
  # Point-in-time recovery so a corrupted lock table is recoverable.
  aws dynamodb update-continuous-backups --table-name "${LOCK_TABLE}" \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
    --region "${REGION}"
fi

echo "==> Done. Initialize Terraform with:"
echo "    terraform init -backend-config=env/${ENVIRONMENT}.backend.hcl"
