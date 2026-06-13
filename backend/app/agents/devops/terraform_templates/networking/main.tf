# Networking overlay module
#
# Pre-AF-012-021: consumes the manually-provisioned foundation VPC + subnets,
# passed in as variables sourced from app.core.config.Settings.foundation_*.
#
# Post-AF-012-021: switch the data sources below to terraform_remote_state
# against Asit's foundation module.

data "aws_vpc" "foundation" {
  id = var.vpc_id
}

data "aws_subnet" "private" {
  for_each = toset(var.private_subnet_ids)
  id       = each.value
}

data "aws_subnet" "public" {
  for_each = toset(var.public_subnet_ids)
  id       = each.value
}

# Per-tenant security groups. Names are derived from organization_id so two
# tenants land in distinct SGs even though they share the VPC.
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.organization_id}-ecs-tasks"
  description = "ECS task SG for tenant ${var.organization_id}"
  vpc_id      = data.aws_vpc.foundation.id
}

resource "aws_security_group" "alb" {
  name        = "${var.organization_id}-alb"
  description = "ALB SG for tenant ${var.organization_id}"
  vpc_id      = data.aws_vpc.foundation.id
}

resource "aws_security_group" "rds" {
  name        = "${var.organization_id}-rds"
  description = "RDS SG for tenant ${var.organization_id}"
  vpc_id      = data.aws_vpc.foundation.id
}

resource "aws_security_group" "redis" {
  name        = "${var.organization_id}-redis"
  description = "ElastiCache SG for tenant ${var.organization_id}"
  vpc_id      = data.aws_vpc.foundation.id
}