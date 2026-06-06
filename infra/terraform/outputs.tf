# Surface the networking outputs at the root so downstream modules/tooling
# (ecs, alb, elasticache) and CI can consume them.

output "vpc_id" {
  description = "ID of the platform VPC."
  value       = module.networking.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the platform VPC."
  value       = module.networking.vpc_cidr_block
}

output "availability_zones" {
  description = "AZs the network spans."
  value       = module.networking.availability_zones
}

output "public_subnet_ids" {
  description = "Public subnet IDs (ALB, NAT)."
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs (ECS tasks, ElastiCache, interface endpoints)."
  value       = module.networking.private_subnet_ids
}

output "nat_public_ips" {
  description = "NAT gateway public IPs (use for third-party egress allow-lists)."
  value       = module.networking.nat_public_ips
}

output "vpc_endpoint_security_group_id" {
  description = "Security group guarding the interface VPC endpoints."
  value       = module.networking.vpc_endpoint_security_group_id
}

output "interface_endpoint_ids" {
  description = "Interface VPC endpoint IDs by service."
  value       = module.networking.interface_endpoint_ids
}

# --- Secrets / KMS (AF-020) -------------------------------------------------

output "kms_key_arn" {
  description = "Platform CMK ARN."
  value       = module.secrets.kms_key_arn
}

output "secret_arns" {
  description = "Map of secret key -> Secrets Manager secret ARN (values populated out-of-band)."
  value       = module.secrets.secret_arns
}

# --- IAM (AF-019) -----------------------------------------------------------

output "task_execution_role_arn" {
  description = "ECS task execution role ARN (for task definitions)."
  value       = module.iam.task_execution_role_arn
}

output "task_role_arns" {
  description = "Map of service name -> ECS task role ARN."
  value       = module.iam.task_role_arns
}
