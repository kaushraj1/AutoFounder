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
