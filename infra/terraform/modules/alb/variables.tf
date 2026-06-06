variable "name_prefix" {
  description = "Resource name prefix, e.g. autofounder-ai-staging."
  type        = string
}

variable "environment" {
  description = "Environment slug (staging | production) — used for the 32-char-limited target-group names."
  type        = string
}

variable "vpc_id" {
  description = "VPC the ALB and target groups live in."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnets for the internet-facing ALB (>= 2 AZs)."
  type        = list(string)
}

variable "services" {
  description = "Per-service ALB config. host_header routes that service; the default_service catches everything else."
  type = map(object({
    port              = number
    health_check_path = optional(string, "/")
    host_header       = optional(string, "")
    priority          = optional(number)
  }))
}

variable "default_service" {
  description = "Service whose target group receives unmatched traffic (e.g. hitting the ALB DNS directly)."
  type        = string
  default     = "backend"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the HTTPS listener. If null, the ALB serves plain HTTP (bring-up only) — supply a cert for production."
  type        = string
  default     = null
}

variable "ssl_policy" {
  description = "TLS policy for the HTTPS listener."
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
}

variable "ingress_cidrs" {
  description = "CIDRs allowed to reach the ALB. Lock down to CloudFront/known ranges in production."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "idle_timeout" {
  description = "ALB idle timeout (seconds)."
  type        = number
  default     = 60
}

variable "enable_deletion_protection" {
  description = "Protect the ALB from accidental deletion (recommend true in production)."
  type        = bool
  default     = false
}

variable "enable_waf" {
  description = "Attach a regional WAFv2 web ACL (AWS managed rule groups) to the ALB."
  type        = bool
  default     = true
}

variable "waf_rate_limit" {
  description = "WAFv2 rate-based rule: max requests per 5-min window per source IP before blocking."
  type        = number
  default     = 2000
}

variable "access_logs_bucket" {
  description = "S3 bucket for ALB access logs (provisioned by AF-016). null disables access logging."
  type        = string
  default     = null
}

variable "health_check" {
  description = "Shared target-group health-check tuning."
  type = object({
    healthy_threshold   = optional(number, 3)
    unhealthy_threshold = optional(number, 3)
    interval            = optional(number, 30)
    timeout             = optional(number, 5)
    matcher             = optional(string, "200-399")
  })
  default = {}
}

variable "tags" {
  description = "Extra tags (platform tags come from provider default_tags)."
  type        = map(string)
  default     = {}
}
