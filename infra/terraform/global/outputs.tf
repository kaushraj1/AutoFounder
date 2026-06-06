output "ecr_repository_urls" {
  description = "Service name -> ECR repository URL (docker push/pull target)."
  value       = module.ecr.repository_urls
}

output "ecr_repository_arns" {
  description = "Service name -> ECR repository ARN."
  value       = module.ecr.repository_arns
}

output "ecr_registry_id" {
  description = "ECR registry (account) ID — the ECR_REGISTRY host prefix is <id>.dkr.ecr.<region>.amazonaws.com."
  value       = module.ecr.registry_id
}
