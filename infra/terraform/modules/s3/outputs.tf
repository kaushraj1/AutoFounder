output "bucket_ids" {
  description = "Map of purpose -> bucket id (name). Includes the audit bucket."
  value = merge(
    { for purpose, b in aws_s3_bucket.standard : purpose => b.id },
    { "audit" = aws_s3_bucket.audit.id },
  )
}

output "bucket_arns" {
  description = "Map of purpose -> bucket ARN. Includes the audit bucket."
  value = merge(
    { for purpose, b in aws_s3_bucket.standard : purpose => b.arn },
    { "audit" = aws_s3_bucket.audit.arn },
  )
}

output "audit_bucket_id" {
  description = "Id (name) of the Object-Lock audit bucket."
  value       = aws_s3_bucket.audit.id
}
