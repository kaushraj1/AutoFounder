variable "name_prefix" {
  description = "Resource name prefix, e.g. autofounder-ai-staging. Bucket names append the purpose and account id for global uniqueness."
  type        = string
}

variable "kms_key_arn" {
  description = "KMS CMK ARN for SSE-KMS encryption at rest. When null, buckets fall back to SSE-S3 (AES256)."
  type        = string
  default     = null
}

variable "audit_retention_years" {
  description = "S3 Object Lock COMPLIANCE retention (years) applied to the audit bucket. Cannot be reduced once objects are locked."
  type        = number
  default     = 7
}

variable "force_destroy" {
  description = "Allow Terraform to delete non-empty buckets on destroy. Keep false in production. Has no effect on Object-Lock-protected objects in the audit bucket."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Extra tags (platform tags come from provider default_tags)."
  type        = map(string)
  default     = {}
}
