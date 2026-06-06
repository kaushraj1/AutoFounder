# Partial S3 backend config for the account-global stack.
#   terraform init -backend-config=global.backend.hcl
# Create the bucket first:  ../scripts/bootstrap-state.sh global
bucket = "autofounder-ai-tfstate-global"
key    = "global/terraform.tfstate"
