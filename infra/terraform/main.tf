# ---------------------------------------------------------------------------
# Root composition for the AutoFounder AI platform infrastructure.
# AF-012 wires the networking module. Subsequent infra tasks (AF-013 ecs,
# AF-015 elasticache, AF-016 s3, AF-018 alb, ...) add their module blocks here.
# ---------------------------------------------------------------------------

module "networking" {
  source = "./modules/networking"

  name_prefix              = local.name_prefix
  vpc_cidr                 = var.vpc_cidr
  az_count                 = var.az_count
  single_nat_gateway       = var.single_nat_gateway
  enable_flow_logs         = var.enable_flow_logs
  flow_logs_retention_days = var.flow_logs_retention_days

  # interface_endpoint_services defaults to ecr.api, ecr.dkr, secretsmanager
  # (the AF-012 requirement). Add logs/sts/kms here as later services need them.
}

# AF-020 — per-environment KMS CMK + Secrets Manager secret containers.
module "secrets" {
  source = "./modules/secrets"

  name_prefix = local.name_prefix
  project     = var.project
  environment = var.environment
}

# AF-019 — least-privilege ECS task execution role + per-service task roles.
# Consumes the CMK + secret prefix from `secrets`; ECR repos (global stack) are
# referenced by constructed ARN, so there is no cross-stack state dependency.
module "iam" {
  source = "./modules/iam"

  name_prefix          = local.name_prefix
  project              = var.project
  services             = var.services
  ecr_repository_names = var.ecr_repository_names
  secret_arn_prefix    = module.secrets.secret_arn_prefix
  kms_key_arn          = module.secrets.kms_key_arn
}
