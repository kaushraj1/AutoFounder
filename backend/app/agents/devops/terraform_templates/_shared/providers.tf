provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project        = "autofounder-ai"
      OrganizationId = var.organization_id
      RunId          = var.run_id
      ManagedBy      = "devops-agent"
    }
  }
}
