variable "aws_region" {
  description = "AWS region for global resources (ECR registry is regional)."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Project slug used in names and the project tag."
  type        = string
  default     = "autofounder-ai"
}

variable "team" {
  description = "Owning team (team tag)."
  type        = string
  default     = "platform"
}

variable "ecr_repository_names" {
  description = "Service names to create shared ECR repositories for. MUST stay in sync with the per-env stack's ecr_repository_names (which builds the IAM pull ARNs) — drift causes a silent ImagePull failure at deploy time."
  type        = list(string)
  default     = ["backend", "web"]
}
