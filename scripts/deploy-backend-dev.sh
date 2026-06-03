#!/usr/bin/env bash
# Build the backend image and push it to AWS ECR (dev tag).
# Requires: Docker, AWS CLI v2, and AWS credentials with ECR push permission.
set -euo pipefail

cd "$(dirname "$0")/.."

: "${AWS_ECR_REGISTRY:?Set AWS_ECR_REGISTRY (e.g. 123456789.dkr.ecr.ap-south-1.amazonaws.com)}"
: "${AWS_REGION_PRIMARY:=ap-south-1}"

IMAGE="${AWS_ECR_REGISTRY}/autofounder-ai-backend:dev"

echo "==> Building ${IMAGE}"
docker build -t "${IMAGE}" AUTOFOUNDER-BACKEND

echo "==> Logging in to ECR (${AWS_REGION_PRIMARY})"
aws ecr get-login-password --region "${AWS_REGION_PRIMARY}" \
  | docker login --username AWS --password-stdin "${AWS_ECR_REGISTRY}"

echo "==> Pushing ${IMAGE}"
docker push "${IMAGE}"

echo "Done. Roll out via CodeDeploy / ECS service update (automated in Phase 4)."
