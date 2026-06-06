variable "name_prefix" {
  description = "Resource name prefix, e.g. autofounder-ai-staging."
  type        = string
}

variable "pillar_queue_names" {
  description = "Per-pillar SQS work queue base names; each gets a main queue + a matching DLQ."
  type        = list(string)
  default = [
    "strategy",
    "research",
    "product-planner",
    "architect",
    "coder",
    "reviewer",
    "devops",
    "marketing",
    "llmops",
  ]
}

variable "sns_kms_master_key_id" {
  description = "KMS key id/alias for SNS server-side encryption. Defaults to the AWS-managed SNS key; pass the platform CMK alias for stricter control."
  type        = string
  default     = "alias/aws/sns"
}

variable "tags" {
  description = "Extra tags (platform tags come from provider default_tags)."
  type        = map(string)
  default     = {}
}
