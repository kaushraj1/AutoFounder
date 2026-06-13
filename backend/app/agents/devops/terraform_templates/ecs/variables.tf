variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "organization_id" {
  type = string
}

variable "run_id" {
  type = string
}

variable "capacity_providers" {
  description = "Fargate capacity providers, in priority order."
  type        = list(string)
  default     = ["FARGATE", "FARGATE_SPOT"]
}

variable "services" {
  description = "Service manifests from CoderOutput.services[]. Keyed by name."
  type = map(object({
    image_uri         = string
    container_port    = number
    desired_count     = number
    cpu               = number
    memory_mb         = number
    health_check_path = string
    env_secret_refs   = list(string)
  }))
  default = {}
}

variable "log_retention_days" {
  type    = number
  default = 90
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "ecs_tasks_security_group_id" {
  type = string
}