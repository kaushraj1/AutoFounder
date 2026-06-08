output "kms_key_arn" {
  description = "ARN of the platform CMK (grant kms:Decrypt to task execution roles)."
  value       = aws_kms_key.this.arn
}

output "kms_key_id" {
  description = "ID of the platform CMK."
  value       = aws_kms_key.this.key_id
}

output "kms_alias_name" {
  description = "Alias of the platform CMK."
  value       = aws_kms_alias.this.name
}

output "secret_arns" {
  description = "Map of secret key -> Secrets Manager secret ARN."
  value       = { for k, s in aws_secretsmanager_secret.this : k => s.arn }
}

output "secret_arn_prefix" {
  description = "Wildcard ARN covering all of this environment's secrets — for least-privilege IAM (secretsmanager:GetSecretValue)."
  value       = "arn:${data.aws_partition.current.partition}:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project}/${var.environment}/*"
}
