variable "project" {
  description = "Project slug; repositories are named <project>/<service>, e.g. autofounder-ai/backend."
  type        = string
  default     = "autofounder-ai"
}

variable "repository_names" {
  description = "Service names to create ECR repositories for (one repo per service, shared across environments — images promoted by digest)."
  type        = list(string)
  default     = ["backend", "web"]
}

variable "image_tag_mutability" {
  description = "MUTABLE allows moving tags like staging-latest/prod-latest; IMMUTABLE is preferred with digest-based deploys (revisit in AF-022)."
  type        = string
  default     = "MUTABLE"

  validation {
    condition     = contains(["MUTABLE", "IMMUTABLE"], var.image_tag_mutability)
    error_message = "image_tag_mutability must be MUTABLE or IMMUTABLE."
  }
}

variable "scan_on_push" {
  description = "Enable image vulnerability scanning on push."
  type        = bool
  default     = true
}

variable "encryption_type" {
  description = "ECR encryption: AES256 (SSE-S3) or KMS. Shared repos use AES256 (per-env CMKs do not apply to a cross-env resource)."
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "KMS"], var.encryption_type)
    error_message = "encryption_type must be AES256 or KMS."
  }
}

variable "kms_key_arn" {
  description = "KMS key ARN when encryption_type = KMS. Ignored for AES256."
  type        = string
  default     = null
}

variable "max_tagged_images" {
  description = "Keep at most this many tagged images per repository (lifecycle policy)."
  type        = number
  default     = 20
}

variable "untagged_expire_days" {
  description = "Expire untagged images older than this many days."
  type        = number
  default     = 14
}

variable "tags" {
  description = "Extra tags (platform tags come from provider default_tags)."
  type        = map(string)
  default     = {}
}
