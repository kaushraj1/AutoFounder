# ---------------------------------------------------------------------------
# ECS (AF-013) — Fargate cluster, one task definition + service per app service,
# wired to the IAM roles (AF-019), ECR images (global stack), Secrets Manager
# (AF-020), and ALB target groups (AF-018). Autoscaling lives in autoscaling.tf.
#
# Log groups use CloudWatch's default at-rest encryption (AWS-managed key). CMK
# encryption is a follow-up: it requires the platform CMK key policy to grant
# the logs.<region>.amazonaws.com service principal, which the secrets module
# does not yet do.
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

locals {
  ecr_registry = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"

  service_images = {
    for svc, cfg in var.services : svc => "${local.ecr_registry}/${var.project}/${svc}:${cfg.image_tag}"
  }
}

resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cluster"
  })
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    base              = 1
    weight            = 1
  }
}

# --- Per-service log group --------------------------------------------------

resource "aws_cloudwatch_log_group" "this" {
  for_each = var.services

  name              = "/ecs/${var.name_prefix}/${each.key}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "/ecs/${var.name_prefix}/${each.key}"
  })
}

# --- Per-service security group (only the ALB may reach the container port) --

resource "aws_security_group" "service" {
  for_each = var.services

  name_prefix = "${var.name_prefix}-${each.key}-svc-"
  description = "ECS service ${each.key} — ingress from the ALB only"
  vpc_id      = var.vpc_id

  ingress {
    description     = "From ALB on the container port"
    from_port       = each.value.port
    to_port         = each.value.port
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
  }

  egress {
    description = "All outbound (image pulls via VPC endpoints, secrets, upstreams)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.key}-svc"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# --- Task definitions -------------------------------------------------------

resource "aws_ecs_task_definition" "this" {
  for_each = var.services

  family                   = "${var.name_prefix}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arns[each.key]

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = each.key
      image     = local.service_images[each.key]
      essential = true

      portMappings = [
        {
          containerPort = each.value.port
          protocol      = "tcp"
        },
      ]

      environment = [
        for k, v in each.value.container_environment : { name = k, value = v }
      ]

      secrets = [
        for key in each.value.secret_keys : {
          name      = upper(replace(replace(key, "/", "_"), "-", "_"))
          valueFrom = var.secret_arns[key]
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.this[each.key].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = each.key
        }
      }
    }
  ])

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.key}"
  })
}

# --- Services ---------------------------------------------------------------

resource "aws_ecs_service" "this" {
  for_each = var.services

  name            = each.key
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.this[each.key].arn
  desired_count   = each.value.desired_count
  launch_type     = "FARGATE"

  health_check_grace_period_seconds = 60

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.service[each.key].id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.alb_target_group_arns[each.key]
    container_name   = each.key
    container_port   = each.value.port
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.key}"
  })

  # desired_count is managed by Application Auto Scaling after the first apply.
  lifecycle {
    ignore_changes = [desired_count]
  }
}
