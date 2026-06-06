variable "name_prefix" {
  description = "Resource name prefix, e.g. autofounder-ai-staging."
  type        = string
}

variable "project" {
  description = "Project slug; secrets are named <project>/<environment>/<key>."
  type        = string
  default     = "autofounder-ai"
}

variable "environment" {
  description = "Environment slug used in the secret path (staging | production)."
  type        = string
}

variable "secret_keys" {
  description = "Secret keys to create as Secrets Manager containers (VALUES are NOT managed by Terraform — populate out-of-band). Named <project>/<environment>/<key>."
  type        = list(string)
  default = [
    "supabase/service_role_key",
    "supabase/jwt_secret",
    "gemini/api_key",
    "stripe/secret_key",
    "stripe/webhook_secret",
    "langsmith/api_key",
    "sentry/dsn_backend",
    "sentry/dsn_frontend",
    "confluent/bootstrap_servers",
    "confluent/api_key",
  ]
}

variable "kms_deletion_window_days" {
  description = "Waiting period before the KMS CMK is deleted."
  type        = number
  default     = 30
}

variable "secret_recovery_window_days" {
  description = "Recovery window before a deleted secret is permanently removed (0 = force-delete, not recommended)."
  type        = number
  default     = 7
}

variable "tags" {
  description = "Extra tags (platform tags come from provider default_tags)."
  type        = map(string)
  default     = {}
}
