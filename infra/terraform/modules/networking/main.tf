# ---------------------------------------------------------------------------
# Networking module — VPC, multi-AZ public/private subnets, NAT gateways,
# internet gateway, and route tables. VPC endpoints live in vpc_endpoints.tf;
# flow logs live in flow_logs.tf.
# ---------------------------------------------------------------------------

data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

locals {
  # Span the first `az_count` available AZs in the region.
  azs = slice(data.aws_availability_zones.available.names, 0, var.az_count)

  # Reserve CIDR space for up to 3 AZs per tier so adding an AZ never renumbers
  # existing subnets. With a /16 VPC and 4 new bits, each subnet is a /20.
  max_azs             = 3
  subnet_newbits      = 4
  public_netnum_base  = 0             # public  -> /20 blocks 0..2
  private_netnum_base = local.max_azs # private -> /20 blocks 3..5

  # Single shared NAT (staging) vs one-per-AZ (production HA).
  nat_gateway_count = var.single_nat_gateway ? 1 : var.az_count
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc"
  })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-igw"
  })
}

# --- Public subnets (ALB, NAT gateways) ------------------------------------

resource "aws_subnet" "public" {
  count = var.az_count

  vpc_id                  = aws_vpc.this.id
  availability_zone       = local.azs[count.index]
  cidr_block              = cidrsubnet(var.vpc_cidr, local.subnet_newbits, local.public_netnum_base + count.index)
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-${local.azs[count.index]}"
    tier = "public"
  })
}

# --- Private subnets (ECS Fargate tasks, ElastiCache, interface endpoints) --

resource "aws_subnet" "private" {
  count = var.az_count

  vpc_id            = aws_vpc.this.id
  availability_zone = local.azs[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr, local.subnet_newbits, local.private_netnum_base + count.index)

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-${local.azs[count.index]}"
    tier = "private"
  })
}

# --- NAT gateways (egress for private subnets) ------------------------------

resource "aws_eip" "nat" {
  count = local.nat_gateway_count

  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-eip-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.this]
}

resource "aws_nat_gateway" "this" {
  count = local.nat_gateway_count

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.this]
}

# --- Public route table (one, shared) --------------------------------------

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-rt"
  })
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  count = var.az_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# --- Private route tables (one per AZ so each can use its local NAT) --------

resource "aws_route_table" "private" {
  count = var.az_count

  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-rt-${local.azs[count.index]}"
  })
}

resource "aws_route" "private_nat" {
  count = var.az_count

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  # With a single shared NAT, every private RT routes through NAT[0];
  # otherwise each AZ routes through its own NAT.
  nat_gateway_id = aws_nat_gateway.this[var.single_nat_gateway ? 0 : count.index].id
}

resource "aws_route_table_association" "private" {
  count = var.az_count

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Lock down the VPC's default security group — no ingress/egress rules
# (CIS AWS EC2.2). Declaring it with no rule blocks makes Terraform strip the
# default allow-all-intra-SG rule AWS creates with every VPC.
resource "aws_default_security_group" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-default-sg-locked"
  })
}
