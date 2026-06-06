output "cluster_name" {
  description = "ECS cluster name (used by the deploy workflows / CodeDeploy)."
  value       = aws_ecs_cluster.this.name
}

output "cluster_arn" {
  description = "ECS cluster ARN."
  value       = aws_ecs_cluster.this.arn
}

output "service_names" {
  description = "Map of service key -> ECS service name."
  value       = { for k, s in aws_ecs_service.this : k => s.name }
}

output "task_definition_arns" {
  description = "Map of service key -> task definition ARN."
  value       = { for k, t in aws_ecs_task_definition.this : k => t.arn }
}

output "service_security_group_ids" {
  description = "Map of service key -> service security group ID."
  value       = { for k, sg in aws_security_group.service : k => sg.id }
}

output "log_group_names" {
  description = "Map of service key -> CloudWatch log group name."
  value       = { for k, lg in aws_cloudwatch_log_group.this : k => lg.name }
}
