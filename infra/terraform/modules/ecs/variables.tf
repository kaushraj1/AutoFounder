variable "name_prefix" {
  description = "Resource name prefix, e.g. autofounder-ai-staging."
  type        = string
}

variable "project" {
  description = "Project slug — used to build the ECR image URL (project/service)."
  type        = string
  default     = "autofounder-ai"
}

variable "aws_region" {
  description = "Region (for the ECR image host and awslogs)."
  type        = string
}

variable "vpc_id" {
  description = "VPC the ECS service security groups live in."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnets the Fargate tasks run in (no public IP)."
  type        = list(string)
}

variable "task_execution_role_arn" {
  description = "Shared ECS task execution role ARN (from the iam module)."
  type        = string
}

variable "task_role_arns" {
  description = "Map of service name -> task role ARN (from the iam module)."
  type        = map(string)
}

variable "alb_target_group_arns" {
  description = "Map of service name -> ALB target group ARN (from the alb module)."
  type        = map(string)
}

variable "alb_security_group_id" {
  description = "ALB security group — allowed as ingress on each service's SG."
  type        = string
}

variable "secret_arns" {
  description = "Map of secret key -> Secrets Manager ARN (from the secrets module), for container secret injection."
  type        = map(string)
  default     = {}
}

variable "services" {
  description = "Per-service ECS config. secret_keys must exist in secret_arns; each becomes an UPPER_SNAKE env var injected from Secrets Manager."
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
  }))
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention for ECS task logs."
  type        = number
  default     = 30
}

variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights on the cluster."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Extra tags (platform tags come from provider default_tags)."
  type        = map(string)
  default     = {}
}
