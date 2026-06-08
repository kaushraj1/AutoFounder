terraform {
  # Remote state in S3 with DynamoDB state locking (per spec: deployment.md).
  # `bucket` and `key` are environment-specific and supplied at init time via a
  # partial backend config, so one set of code serves every environment:
  #
  #   terraform init -backend-config=env/staging.backend.hcl
  #   terraform init -backend-config=env/production.backend.hcl
  #
  # The state bucket + lock table must exist first — run scripts/bootstrap-state.*
  backend "s3" {
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "autofounder-ai-tfstate-lock"
  }
}
