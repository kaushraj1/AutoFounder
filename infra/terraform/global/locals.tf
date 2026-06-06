locals {
  # env = "global" marks account-wide resources shared by every environment.
  common_tags = {
    env        = "global"
    project    = var.project
    managed-by = "terraform"
    team       = var.team
  }
}
