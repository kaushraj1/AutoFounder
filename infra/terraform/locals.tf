locals {
  name_prefix = "${var.project}-${var.environment}"

  # The four platform tags required on every resource (deployment.md).
  common_tags = {
    env        = var.environment
    project    = var.project
    managed-by = "terraform"
    team       = var.team
  }
}
