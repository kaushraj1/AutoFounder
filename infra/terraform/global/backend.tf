terraform {
  # Account-global state — a single shared backend (not per environment).
  #   terraform init -backend-config=global.backend.hcl
  backend "s3" {
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "autofounder-ai-tfstate-lock"
  }
}
