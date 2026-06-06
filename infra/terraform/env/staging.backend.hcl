# Partial S3 backend config for staging.
#   terraform init -backend-config=env/staging.backend.hcl
bucket = "autofounder-ai-tfstate-staging"
key    = "platform/terraform.tfstate"
