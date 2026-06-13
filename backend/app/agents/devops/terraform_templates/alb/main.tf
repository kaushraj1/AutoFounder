# Application Load Balancer + per-service target groups + listener rules.

resource "aws_lb" "this" {
  name               = substr("${var.organization_id}-alb", 0, 32)
  load_balancer_type = "application"
  subnets            = var.public_subnet_ids
  security_groups    = [var.alb_security_group_id]
  internal           = false
}

resource "aws_lb_target_group" "service" {
  for_each = var.services

  name        = substr("${var.organization_id}-${each.key}", 0, 32)
  port        = each.value.container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    path                = each.value.health_check_path
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

# HTTPS listener — the certificate ARN is filled in by the DevOps agent
# after the configure_dns_ssl node provisions the ACM cert.
# resource "aws_lb_listener" "https" { ... }