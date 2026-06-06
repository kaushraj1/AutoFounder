output "task_execution_role_arn" {
  description = "ARN of the shared ECS task execution role (set as executionRoleArn in task definitions)."
  value       = aws_iam_role.task_execution.arn
}

output "task_execution_role_name" {
  description = "Name of the shared ECS task execution role."
  value       = aws_iam_role.task_execution.name
}

output "task_role_arns" {
  description = "Map of service name -> task role ARN (set as taskRoleArn per service)."
  value       = { for k, r in aws_iam_role.task : k => r.arn }
}

output "task_role_names" {
  description = "Map of service name -> task role name."
  value       = { for k, r in aws_iam_role.task : k => r.name }
}
