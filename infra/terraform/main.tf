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
  services             = keys(var.services)
  ecr_repository_names = keys(var.services)
  secret_arn_prefix    = module.secrets.secret_arn_prefix
  kms_key_arn          = module.secrets.kms_key_arn
}

# AF-018 — Application Load Balancer + WAF + per-service target groups.
module "alb" {
  source = "./modules/alb"

  name_prefix       = local.name_prefix
  environment       = var.environment
  vpc_id            = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  default_service   = var.default_service
  certificate_arn   = var.certificate_arn
  enable_waf        = var.enable_waf

  # Production fails closed without a cert (precondition in the alb module) and
  # is protected from accidental deletion.
  enable_deletion_protection = var.environment == "production"

  services = {
    for k, v in var.services : k => {
      port              = v.port
      health_check_path = v.health_check_path
      host_header       = v.host_header
      priority          = v.priority
    }
  }
}

# AF-013 — ECS Fargate cluster + services, wired to IAM roles, ECR images,
# Secrets Manager, and the ALB target groups.
module "ecs" {
  source = "./modules/ecs"

  name_prefix             = local.name_prefix
  project                 = var.project
  aws_region              = var.aws_region
  vpc_id                  = module.networking.vpc_id
  private_subnet_ids      = module.networking.private_subnet_ids
  task_execution_role_arn = module.iam.task_execution_role_arn
  task_role_arns          = module.iam.task_role_arns
  alb_target_group_arns   = module.alb.target_group_arns
  alb_security_group_id   = module.alb.alb_security_group_id
  secret_arns             = module.secrets.secret_arns

  # ECS services attach to ALB target groups, which must already be associated
  # with a listener — force the whole ALB module to settle first.
  depends_on = [module.alb]

  services = {
    for k, v in var.services : k => {
      port                  = v.port
      cpu                   = v.cpu
      memory                = v.memory
      desired_count         = v.desired_count
      image_tag             = v.image_tag
      container_environment = v.container_environment
      secret_keys           = v.secret_keys
      min_capacity          = v.min_capacity
      max_capacity          = v.max_capacity
      cpu_target            = v.cpu_target
      memory_target         = v.memory_target
    }
  }
}

# AF-015 — ElastiCache Redis (LangGraph checkpoint hot cache, semantic prompt
# cache, embedding cache, per-tenant cost accumulator).
module "elasticache" {
  source = "./modules/elasticache"

  name_prefix        = local.name_prefix
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  vpc_cidr           = var.vpc_cidr
  node_type          = var.redis_node_type
  # At-rest uses the AWS-managed ElastiCache key. CMK-at-rest is a follow-up: it
  # needs a key policy on the secrets CMK granting elasticache.amazonaws.com
  # kms:Decrypt+CreateGrant — the default root-only policy denies the service,
  # which would fail the replication-group create.
}

# AF-016 — S3 buckets (artifacts, RLHF data lake, prompt templates, audit w/ Object Lock).
module "s3" {
  source = "./modules/s3"

  name_prefix = local.name_prefix
  kms_key_arn = module.secrets.kms_key_arn
}

# AF-017 — EventBridge bus + per-pillar SQS queues (+DLQs) + gate-decisions queue + SNS.
module "messaging" {
  source = "./modules/messaging"

  name_prefix = local.name_prefix
}
