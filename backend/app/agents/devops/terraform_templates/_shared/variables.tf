variable "aws_region" {
  description = "AWS region for all per-tenant resources."
  type        = string
  default     = "ap-south-1"
}

variable "organization_id" {
  description = "Tenant identifier. Used in tags and resource name prefixes."
  type        = string
}

variable "run_id" {
  description = "Orchestrator run_id. Used for traceability tags."
  type        = string
}
