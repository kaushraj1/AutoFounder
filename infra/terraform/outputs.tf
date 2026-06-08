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

# --- ALB (AF-018) -----------------------------------------------------------

output "alb_dns_name" {
  description = "ALB DNS name — create Route 53 ALIAS records (api./app.) pointing here."
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "ALB hosted zone ID (for Route 53 ALIAS records)."
  value       = module.alb.alb_zone_id
}

output "web_acl_arn" {
  description = "WAF web ACL ARN (null when WAF disabled)."
  value       = module.alb.web_acl_arn
}

# --- ECS (AF-013) -----------------------------------------------------------

output "ecs_cluster_name" {
  description = "ECS cluster name (target for the deploy workflows)."
  value       = module.ecs.cluster_name
}

output "ecs_service_names" {
  description = "Map of service key -> ECS service name."
  value       = module.ecs.service_names
}

# --- ElastiCache (AF-015) ---------------------------------------------------

output "redis_primary_endpoint" {
  description = "ElastiCache Redis primary endpoint (write)."
  value       = module.elasticache.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "ElastiCache Redis reader endpoint."
  value       = module.elasticache.reader_endpoint_address
}

output "redis_port" {
  description = "ElastiCache Redis port."
  value       = module.elasticache.port
}

# --- S3 (AF-016) ------------------------------------------------------------

output "s3_bucket_ids" {
  description = "Map of bucket purpose -> bucket name."
  value       = module.s3.bucket_ids
}

# --- Messaging (AF-017) -----------------------------------------------------

output "sqs_queue_urls" {
  description = "Map of queue name -> SQS URL (incl. gate-decisions)."
  value       = module.messaging.queue_urls
}

output "sns_topic_arn" {
  description = "SNS notifications topic ARN."
  value       = module.messaging.sns_topic_arn
}

output "event_bus_name" {
  description = "EventBridge custom bus name."
  value       = module.messaging.event_bus_name
}
