# ---------------------------------------------------------------------------
# ElastiCache (AF-015) — a Redis 7 replication group (cluster-mode disabled:
# one primary + read replicas) deployed Multi-AZ across the networking module's
# private subnets, reachable only from inside the VPC on 6379, encrypted at rest
# and in transit. The AUTH token is supplied out-of-band — no secret value is
# generated or persisted into Terraform state.
# ---------------------------------------------------------------------------

# --- Subnet group (private subnets only) -----------------------------------

resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name_prefix}-redis"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis-subnets"
  })
}

# --- Security group (Redis reachable only from within the VPC) --------------

resource "aws_security_group" "this" {
  name_prefix = "${var.name_prefix}-redis-"
  description = "ElastiCache Redis — ingress on 6379 from within the VPC only"
  vpc_id      = var.vpc_id

  ingress {
    description = "Redis from within the VPC"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Replication/cluster traffic within the VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# --- Replication group ------------------------------------------------------

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = "${var.name_prefix}-redis"
  description          = "${var.name_prefix} Redis replication group"

  engine         = "redis"
  engine_version = var.engine_version
  node_type      = var.node_type
  port           = 6379

  # Cluster-mode disabled: a single primary plus (num_cache_clusters - 1) replicas.
  num_cache_clusters         = var.num_cache_clusters
  automatic_failover_enabled = var.automatic_failover_enabled
  multi_az_enabled           = var.multi_az_enabled

  subnet_group_name  = aws_elasticache_subnet_group.this.name
  security_group_ids = [aws_security_group.this.id]

  at_rest_encryption_enabled = var.at_rest_encryption_enabled
  kms_key_id                 = var.at_rest_encryption_enabled ? var.kms_key_arn : null
  transit_encryption_enabled = var.transit_encryption_enabled

  # AUTH token is optional and supplied out-of-band; requires TLS in transit.
  auth_token = var.auth_token

  snapshot_retention_limit = var.snapshot_retention_limit

  # Apply maintenance/version changes in the next maintenance window, not live.
  apply_immediately = false

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis"
  })
}
