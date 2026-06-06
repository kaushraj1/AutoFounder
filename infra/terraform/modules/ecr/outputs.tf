output "repository_urls" {
  description = "Map of service name -> ECR repository URL (push/pull target)."
  value       = { for k, r in aws_ecr_repository.this : k => r.repository_url }
}

output "repository_arns" {
  description = "Map of service name -> ECR repository ARN."
  value       = { for k, r in aws_ecr_repository.this : k => r.arn }
}

output "repository_names" {
  description = "Map of service name -> full ECR repository name (project/service)."
  value       = { for k, r in aws_ecr_repository.this : k => r.name }
}

output "registry_id" {
  description = "ECR registry (account) ID — the ECR_REGISTRY host is <id>.dkr.ecr.<region>.amazonaws.com."
  value       = data.aws_caller_identity.current.account_id
}
