# ---------------------------------------------------------------------------
# VPC endpoints (AF-012) — keep AWS API traffic on the AWS backbone, off the
# public internet, and reduce NAT data-processing cost.
#   * S3              -> Gateway endpoint (free), attached to private route tables.
#   * ECR api + dkr   -> Interface endpoints (image pulls for ECS Fargate).
#   * Secrets Manager -> Interface endpoint (runtime secret injection into tasks).
# ---------------------------------------------------------------------------

# Security group for interface endpoints: allow HTTPS only, from within the VPC.
resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${var.name_prefix}-vpce-"
  description = "HTTPS from within the VPC to interface VPC endpoints"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTPS from VPC CIDR"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.this.cidr_block]
  }

  egress {
    description = "HTTPS return traffic within VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.this.cidr_block]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpce-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# S3 — Gateway endpoint, associated with all private route tables.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-s3-endpoint"
  })
}

# Interface endpoints (ECR api/dkr, Secrets Manager, plus anything passed in).
resource "aws_vpc_endpoint" "interface" {
  for_each = toset(var.interface_endpoint_services)

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${each.value}-endpoint"
  })
}
