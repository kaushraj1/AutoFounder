# ---------------------------------------------------------------------------
# Account-global composition. Resources here are shared by every environment
# and must exist exactly once per account (not per env). Currently: ECR.
# Future global resources (e.g. the GitHub Actions OIDC provider for AF-022)
# are added here.
# ---------------------------------------------------------------------------

module "ecr" {
  source = "../modules/ecr"

  project          = var.project
  repository_names = var.ecr_repository_names
}
