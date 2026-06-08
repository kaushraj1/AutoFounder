terraform {
  backend "s3" {}
}
# Key pattern: {organization_id}/{run_id}/{module}.tfstate