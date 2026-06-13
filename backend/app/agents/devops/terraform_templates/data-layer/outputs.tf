output "db_endpoint" {
  value = aws_db_instance.this.endpoint
}

output "db_credentials_secret_arn" {
  value = aws_secretsmanager_secret.db_credentials.arn
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.this.cache_nodes[0].address
}

output "artefact_bucket_name" {
  value = aws_s3_bucket.artefacts.bucket
}