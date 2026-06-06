# ---------------------------------------------------------------------------
# S3 (AF-016) — platform object storage buckets:
#   - artifacts         : generated MVP artifacts / build outputs
#   - data-lake         : RLHF datasets and analytics data
#   - prompt-templates  : versioned prompt templates
#   - audit             : audit logs, WORM-protected via S3 Object Lock
#
# Bucket names are globally unique: "${name_prefix}-<purpose>-<account_id>".
# Encryption at rest is always on (SSE-KMS when kms_key_arn is set, else
# SSE-S3/AES256). Versioning, public-access-block, and lifecycle hygiene
# (abort incomplete multipart @7d, expire noncurrent versions @90d) apply to
# every bucket. Standard buckets are managed via for_each; the audit bucket is
# explicit because Object Lock can only be enabled at bucket creation time.
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_partition" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id

  # Standard (non-Object-Lock) buckets, keyed by purpose.
  standard_purposes = toset([
    "artifacts",
    "data-lake",
    "prompt-templates",
  ])

  audit_purpose = "audit"

  # Globally-unique physical bucket names. AWS hard limit is 63 chars.
  standard_bucket_names = {
    for purpose in local.standard_purposes :
    purpose => "${var.name_prefix}-${purpose}-${local.account_id}"
  }
  audit_bucket_name = "${var.name_prefix}-${local.audit_purpose}-${local.account_id}"

  # SSE-KMS when a CMK is supplied, otherwise SSE-S3.
  use_kms       = var.kms_key_arn != null
  sse_algorithm = local.use_kms ? "aws:kms" : "AES256"
}

# ---------------------------------------------------------------------------
# Standard buckets (artifacts, data-lake, prompt-templates)
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "standard" {
  for_each = local.standard_purposes

  bucket        = local.standard_bucket_names[each.key]
  force_destroy = var.force_destroy

  tags = merge(var.tags, {
    Name = local.standard_bucket_names[each.key]
  })
}

resource "aws_s3_bucket_versioning" "standard" {
  for_each = aws_s3_bucket.standard

  bucket = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "standard" {
  for_each = aws_s3_bucket.standard

  bucket = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = local.sse_algorithm
      kms_master_key_id = local.use_kms ? var.kms_key_arn : null
    }
    bucket_key_enabled = local.use_kms
  }
}

resource "aws_s3_bucket_public_access_block" "standard" {
  for_each = aws_s3_bucket.standard

  bucket = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "standard" {
  for_each = aws_s3_bucket.standard

  bucket = each.value.id

  rule {
    id     = "abort-incomplete-multipart"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  # Lifecycle rules require versioning to be configured first.
  depends_on = [aws_s3_bucket_versioning.standard]
}

# ---------------------------------------------------------------------------
# Audit bucket (WORM via S3 Object Lock — created with object_lock_enabled,
# which mandates versioning). COMPLIANCE mode means even the root account
# cannot delete or shorten retention before it expires.
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "audit" {
  bucket              = local.audit_bucket_name
  force_destroy       = var.force_destroy
  object_lock_enabled = true

  tags = merge(var.tags, {
    Name = local.audit_bucket_name
  })
}

resource "aws_s3_bucket_versioning" "audit" {
  bucket = aws_s3_bucket.audit.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "audit" {
  bucket = aws_s3_bucket.audit.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = local.sse_algorithm
      kms_master_key_id = local.use_kms ? var.kms_key_arn : null
    }
    bucket_key_enabled = local.use_kms
  }
}

resource "aws_s3_bucket_public_access_block" "audit" {
  bucket = aws_s3_bucket.audit.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_object_lock_configuration" "audit" {
  bucket = aws_s3_bucket.audit.id

  rule {
    default_retention {
      mode  = "COMPLIANCE"
      years = var.audit_retention_years
    }
  }

  # Object Lock configuration requires versioning to be enabled.
  depends_on = [aws_s3_bucket_versioning.audit]
}

resource "aws_s3_bucket_lifecycle_configuration" "audit" {
  bucket = aws_s3_bucket.audit.id

  rule {
    id     = "abort-incomplete-multipart"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  depends_on = [aws_s3_bucket_versioning.audit]
}

# ---------------------------------------------------------------------------
# Enforce encryption in transit (deny non-TLS) on every bucket — including the
# WORM audit bucket and the RLHF data lake. A Deny/Principal:* policy does not
# grant public access, so it is permitted under the public-access-block above.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "tls_only" {
  for_each = merge(
    { for k, b in aws_s3_bucket.standard : k => b.arn },
    { (local.audit_purpose) = aws_s3_bucket.audit.arn },
  )

  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [each.value, "${each.value}/*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "standard" {
  for_each = aws_s3_bucket.standard

  bucket = each.value.id
  policy = data.aws_iam_policy_document.tls_only[each.key].json
}

resource "aws_s3_bucket_policy" "audit" {
  bucket = aws_s3_bucket.audit.id
  policy = data.aws_iam_policy_document.tls_only[local.audit_purpose].json
}
