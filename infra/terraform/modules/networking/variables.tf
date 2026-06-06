variable "name_prefix" {
  description = "Prefix applied to all resource names, e.g. autofounder-ai-staging."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.name_prefix))
    error_message = "name_prefix must be lowercase alphanumeric with hyphens only."
  }
}

variable "vpc_cidr" {
  description = "Primary IPv4 CIDR block for the VPC (a /16 is recommended to leave room for /20 subnets)."
  type        = string

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr must be a valid IPv4 CIDR block."
  }
}

variable "az_count" {
  description = "Number of Availability Zones to span (2 minimum for multi-AZ; 3 recommended for production)."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count must be 2 or 3 (the module reserves CIDR space for up to 3 AZs)."
  }
}

variable "single_nat_gateway" {
  description = "If true, provision a single shared NAT gateway (cheaper, lower availability — use for staging). If false, one NAT gateway per AZ (HA — use for production)."
  type        = bool
  default     = false
}

variable "interface_endpoint_services" {
  description = "Short service names for AWS PrivateLink interface VPC endpoints (region is prefixed automatically). Defaults cover the AF-012 requirement: ECR (api + dkr) and Secrets Manager."
  type        = list(string)
  default     = ["ecr.api", "ecr.dkr", "secretsmanager"]
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs to CloudWatch Logs (recommended on for production)."
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "CloudWatch Logs retention for VPC Flow Logs."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Common tags applied to every resource (in addition to provider default_tags)."
  type        = map(string)
  default     = {}
}
