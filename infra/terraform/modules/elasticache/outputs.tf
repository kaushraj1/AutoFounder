output "primary_endpoint_address" {
  description = "Primary (write) endpoint hostname for the Redis replication group."
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "Reader (read-replica) endpoint hostname for the Redis replication group."
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "port" {
  description = "Port Redis listens on."
  value       = aws_elasticache_replication_group.this.port
}

output "security_group_id" {
  description = "ID of the Redis security group (reference it from clients that need egress to Redis)."
  value       = aws_security_group.this.id
}

output "replication_group_id" {
  description = "ID of the Redis replication group."
  value       = aws_elasticache_replication_group.this.id
}
