# ---------------------------------------------------------------------------
# ALB (AF-018) — internet-facing Application Load Balancer, one target group
# per ECS service, HTTP + (optional) HTTPS listeners with host-based routing.
# WAF lives in waf.tf. ACM certificates / Route 53 records are operator-managed
# (pass certificate_arn); this module does not create DNS or validate certs.
# ---------------------------------------------------------------------------

locals {
  serve_https = var.certificate_arn != null

  # Services (other than the default) that have a host_header get a routing rule.
  routed_services = {
    for k, v in var.services : k => v
    if v.host_header != "" && k != var.default_service
  }
}

resource "aws_security_group" "alb" {
  name_prefix = "${var.name_prefix}-alb-"
  description = "Ingress to the ${var.name_prefix} ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.ingress_cidrs
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.ingress_cidrs
  }

  egress {
    description = "To ECS targets in the VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb" "this" {
  name                       = "${var.name_prefix}-alb"
  load_balancer_type         = "application"
  internal                   = false
  security_groups            = [aws_security_group.alb.id]
  subnets                    = var.public_subnet_ids
  idle_timeout               = var.idle_timeout
  enable_deletion_protection = var.enable_deletion_protection
  drop_invalid_header_fields = true

  dynamic "access_logs" {
    for_each = var.access_logs_bucket != null ? [1] : []
    content {
      bucket  = var.access_logs_bucket
      prefix  = var.name_prefix
      enabled = true
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb"
  })

  lifecycle {
    precondition {
      condition     = var.environment != "production" || var.certificate_arn != null
      error_message = "production requires certificate_arn — no plaintext-HTTP ALB in production."
    }
    precondition {
      condition     = alltrue([for k, v in var.services : k == var.default_service || v.host_header != ""])
      error_message = "Every non-default service must set host_header, else its target group is unroutable."
    }
    precondition {
      condition     = alltrue([for k, v in var.services : k == var.default_service || v.priority != null])
      error_message = "Every host-routed (non-default) service must set a listener-rule priority."
    }
    precondition {
      condition     = length([for k, v in var.services : v.priority if k != var.default_service && v.priority != null]) == length(distinct([for k, v in var.services : v.priority if k != var.default_service && v.priority != null]))
      error_message = "Listener-rule priorities must be unique across host-routed services."
    }
  }
}

resource "aws_lb_target_group" "this" {
  for_each = var.services

  name_prefix = substr(each.key, 0, 6) # <=6 chars; create_before_destroy needs a generated suffix
  port        = each.value.port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip" # Fargate awsvpc tasks register by IP

  deregistration_delay = 30

  health_check {
    enabled             = true
    path                = each.value.health_check_path
    protocol            = "HTTP"
    healthy_threshold   = var.health_check.healthy_threshold
    unhealthy_threshold = var.health_check.unhealthy_threshold
    interval            = var.health_check.interval
    timeout             = var.health_check.timeout
    matcher             = var.health_check.matcher
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-${each.key}"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# --- Listeners --------------------------------------------------------------

# Port 80: redirect to HTTPS when a cert exists, otherwise serve traffic.
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = local.serve_https ? [1] : []
    content {
      type = "redirect"
      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  dynamic "default_action" {
    for_each = local.serve_https ? [] : [1]
    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.this[var.default_service].arn
    }
  }
}

# Port 443: only when a certificate is supplied.
resource "aws_lb_listener" "https" {
  count = local.serve_https ? 1 : 0

  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = var.ssl_policy
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this[var.default_service].arn
  }
}

# Host-based routing for non-default services, on whichever listener serves.
resource "aws_lb_listener_rule" "host" {
  for_each = local.routed_services

  listener_arn = local.serve_https ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
  priority     = each.value.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this[each.key].arn
  }

  condition {
    host_header {
      values = [each.value.host_header]
    }
  }
}
