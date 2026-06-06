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
  description = "Single source of truth for app services. The map KEYS are the service names — they equal the ECR repo names (keep in sync with the global stack), the IAM task roles (AF-019), the ALB target groups (AF-018), and the ECS services (AF-013). Each service that is not the default_service MUST set a host_header so its ALB target group is routable."
  type = map(object({
    port                  = number
    cpu                   = optional(number, 512)
    memory                = optional(number, 1024)
    desired_count         = optional(number, 2)
    image_tag             = optional(string, "latest")
    container_environment = optional(map(string), {})
    secret_keys           = optional(list(string), [])
    min_capacity          = optional(number, 2)
    max_capacity          = optional(number, 10)
    cpu_target            = optional(number, 70)
    memory_target         = optional(number, 80)
    health_check_path     = optional(string, "/")
    host_header           = optional(string, "")
    priority              = optional(number)
  }))
  default = {
    backend = { port = 8000, health_check_path = "/health" }
    web     = { port = 3000, host_header = "app.autofounder.ai", priority = 10 }
  }
}

variable "default_service" {
  description = "Service that receives unmatched ALB traffic (must be a key in services)."
  type        = string
  default     = "backend"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the ALB HTTPS listener. null = HTTP only (bring-up); supply a cert for production."
  type        = string
  default     = null
}

variable "enable_waf" {
  description = "Attach WAFv2 AWS-managed rule groups to the ALB."
  type        = bool
  default     = true
}
