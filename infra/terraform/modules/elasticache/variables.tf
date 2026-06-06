variable "name_prefix" {
  description = "Resource name prefix, e.g. autofounder-ai-staging."
  type        = string
}

variable "vpc_id" {
  description = "VPC the ElastiCache cluster and its security group live in (from the networking module)."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the cache subnet group (from the networking module)."
  type        = list(string)
}

variable "vpc_cidr" {
  description = "VPC IPv4 CIDR — the only source allowed to reach Redis on 6379 (from the networking module)."
  type        = string
}

variable "node_type" {
  description = "ElastiCache node instance type."
  type        = string
  default     = "cache.t4g.micro"
}

variable "num_cache_clusters" {
  description = "Total nodes in the replication group (cluster-mode disabled => 1 primary + N-1 read replicas). >= 2 enables failover/Multi-AZ."
  type        = number
  default     = 2
}

variable "engine_version" {
  description = "Redis engine version."
  type        = string
  default     = "7.1"
}

variable "multi_az_enabled" {
  description = "Place replicas in different AZs from the primary (requires num_cache_clusters >= 2 and automatic_failover_enabled)."
  type        = bool
  default     = true
}

variable "automatic_failover_enabled" {
  description = "Promote a replica automatically if the primary fails (requires num_cache_clusters >= 2)."
  type        = bool
  default     = true
}

variable "transit_encryption_enabled" {
  description = "Enable in-transit (TLS) encryption. Required when auth_token is set."
  type        = bool
  default     = true
}

variable "at_rest_encryption_enabled" {
  description = "Enable encryption at rest (uses kms_key_arn when set, otherwise the AWS-managed key)."
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "Optional CMK ARN for at-rest encryption (the platform CMK from the secrets module). Null => AWS-managed key."
  type        = string
  default     = null
}

variable "auth_token" {
  description = "Optional Redis AUTH token (>= 16 chars). Supplied out-of-band; never generated or persisted here. Requires transit_encryption_enabled."
  type        = string
  default     = null
  sensitive   = true
}

variable "snapshot_retention_limit" {
  description = "Days to retain automatic snapshots (0 disables snapshots)."
  type        = number
  default     = 5
}

variable "tags" {
  description = "Extra tags (platform tags come from provider default_tags)."
  type        = map(string)
  default     = {}
}
