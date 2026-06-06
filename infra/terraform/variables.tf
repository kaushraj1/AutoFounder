variable "environment" {
  description = "Deployment environment. Drives naming, CIDR, and tags."
  type        = string

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be one of: staging, production."
  }
}

variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Project slug used in resource names and the project tag."
  type        = string
  default     = "autofounder-ai"
}

variable "team" {
  description = "Owning team (team tag)."
  type        = string
  default     = "platform"
}

variable "vpc_cidr" {
  description = "Primary IPv4 CIDR block for the VPC (use a /16)."
  type        = string
}

variable "az_count" {
  description = "Number of Availability Zones to span (2 for staging, 3 for production)."
  type        = number
  default     = 2
}

variable "single_nat_gateway" {
  description = "Single shared NAT gateway (staging) vs one per AZ (production HA)."
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs to CloudWatch Logs."
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "Retention for VPC Flow Logs in CloudWatch."
  type        = number
  default     = 30
}

variable "services" {
  description = "ECS services that get a dedicated task role (AF-019)."
  type        = list(string)
  default     = ["backend", "web"]
}

variable "ecr_repository_names" {
  description = "Shared ECR repo service names the execution role may pull (must match the global stack's ecr_repository_names)."
  type        = list(string)
  default     = ["backend", "web"]
}
