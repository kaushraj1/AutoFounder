variable "name_prefix" {
  description = "Resource name prefix, e.g. autofounder-ai-staging."
  type        = string
}

variable "project" {
  description = "Project slug — used to construct the shared ECR repository ARNs (project/service)."
  type        = string
  default     = "autofounder-ai"
}

variable "services" {
  description = "ECS services that get a dedicated task role."
  type        = list(string)
  default     = ["backend", "web"]
}

variable "ecr_repository_names" {
  description = "Shared ECR repo service names the execution role may pull (ARNs constructed from account/region/project)."
  type        = list(string)
  default     = ["backend", "web"]
}

variable "secret_arn_prefix" {
  description = "Wildcard ARN of this environment's Secrets Manager secrets (from the secrets module)."
  type        = string
}

variable "kms_key_arn" {
  description = "Platform CMK ARN the execution role may use to decrypt secrets (from the secrets module)."
  type        = string
}

variable "log_group_prefix" {
  description = "CloudWatch Logs path prefix the execution role may write to."
  type        = string
  default     = null
}

variable "task_role_policies" {
  description = "Optional map of service name -> inline IAM policy JSON for that service's task role (app permissions). Services omitted get a role with NO permissions (deny-by-default). Values MUST be least-privilege — never Action/Resource \"*\"; prefer generating the JSON with aws_iam_policy_document."
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Extra tags (platform tags come from provider default_tags)."
  type        = map(string)
  default     = {}
}
