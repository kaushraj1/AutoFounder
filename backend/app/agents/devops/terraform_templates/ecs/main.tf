# ECS Fargate cluster + per-service task definitions.
#
# The DevOps agent fills the `services` map at runtime from CoderOutput.services[]
# (image_uri, port, env_secret_refs, resource_requests, replicas_baseline).

resource "aws_ecs_cluster" "this" {
  name = "${var.organization_id}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = var.capacity_providers
}

resource "aws_cloudwatch_log_group" "services" {
  for_each          = var.services
  name              = "/ecs/${var.organization_id}/${each.key}"
  retention_in_days = var.log_retention_days
}

# Task definitions and services are rendered at runtime by the DevOps agent
# (one aws_ecs_task_definition + aws_ecs_service per entry in var.services)
# and appended to this file before terraform apply. Each service binds to a
# target group from the alb module and uses the SG from networking.