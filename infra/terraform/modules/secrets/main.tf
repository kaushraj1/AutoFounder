# ---------------------------------------------------------------------------
# Secrets (AF-020) — a per-environment KMS CMK for encryption at rest plus
# Secrets Manager secret CONTAINERS for each documented key. Secret VALUES are
# never stored in Terraform/state — operators populate them out-of-band
# (console / `aws secretsmanager put-secret-value`) and rotate by adding a new
# version, then forcing a new ECS deployment.
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_partition" "current" {}

# Customer-managed key for encrypting secrets (and reusable for SSM/S3/logs).
# No explicit key policy => AWS applies the default policy granting the account
# root full access, which keeps the key manageable and avoids lockout.
resource "aws_kms_key" "this" {
  description             = "${var.name_prefix} platform CMK (secrets, params, logs)"
  enable_key_rotation     = true
  deletion_window_in_days = var.kms_deletion_window_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cmk"
  })
}

resource "aws_kms_alias" "this" {
  name          = "alias/${var.name_prefix}"
  target_key_id = aws_kms_key.this.key_id
}

# Secret containers (metadata only — no aws_secretsmanager_secret_version here,
# so no plaintext ever enters Terraform state).
resource "aws_secretsmanager_secret" "this" {
  for_each = toset(var.secret_keys)

  name                    = "${var.project}/${var.environment}/${each.value}"
  description             = "Managed container for ${each.value} (value set out-of-band)"
  kms_key_id              = aws_kms_key.this.arn
  recovery_window_in_days = var.secret_recovery_window_days

  tags = merge(var.tags, {
    Name = "${var.project}/${var.environment}/${each.value}"
  })
}
