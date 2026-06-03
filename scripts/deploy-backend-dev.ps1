# Build the backend image and push it to AWS ECR (dev tag).
# Requires: Docker, AWS CLI v2, and AWS credentials with ECR push permission.
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

if (-not $env:AWS_ECR_REGISTRY) {
    throw "Set AWS_ECR_REGISTRY (e.g. 123456789.dkr.ecr.ap-south-1.amazonaws.com)"
}
$region = if ($env:AWS_REGION_PRIMARY) { $env:AWS_REGION_PRIMARY } else { "ap-south-1" }
$image = "$($env:AWS_ECR_REGISTRY)/autofounder-ai-backend:dev"

Write-Host "==> Building $image"
docker build -t $image backend

Write-Host "==> Logging in to ECR ($region)"
aws ecr get-login-password --region $region | docker login --username AWS --password-stdin $env:AWS_ECR_REGISTRY

Write-Host "==> Pushing $image"
docker push $image

Write-Host "Done. Roll out via CodeDeploy / ECS service update (automated in Phase 4)."
