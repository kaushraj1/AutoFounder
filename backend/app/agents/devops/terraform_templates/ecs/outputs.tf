output "cluster_arn" {
  value = aws_ecs_cluster.this.arn
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "service_log_groups" {
  value = { for k, v in aws_cloudwatch_log_group.services : k => v.name }
}