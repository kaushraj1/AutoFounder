# Partial S3 backend config for production.
#   terraform init -backend-config=env/production.backend.hcl
bucket = "autofounder-ai-tfstate-production"
key    = "platform/terraform.tfstate"
