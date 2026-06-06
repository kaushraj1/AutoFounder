# s3 (AF-016)

Platform object storage for AutoFounder AI. Creates four buckets with
encryption at rest, versioning, public-access blocked, and lifecycle hygiene.
The `audit` bucket is additionally WORM-protected with S3 Object Lock.

## Buckets

| Purpose            | Object Lock | Use                                          |
| ------------------ | ----------- | -------------------------------------------- |
| `artifacts`        | no          | Generated MVP artifacts / build outputs      |
| `data-lake`        | no          | RLHF datasets and analytics data             |
| `prompt-templates` | no          | Versioned prompt templates                   |
| `audit`            | yes         | Audit logs (COMPLIANCE retention, 7 yr)      |

Physical names are globally unique: `${name_prefix}-<purpose>-<account_id>`
(account id resolved from `aws_caller_identity`). The longest name stays within
the 63-character S3 limit.

## Encryption

- `kms_key_arn = null` (default) -> SSE-S3 (`AES256`).
- `kms_key_arn` set -> SSE-KMS (`aws:kms`) with that CMK and S3 Bucket Keys
  enabled to cut KMS request cost.

No secret values are written to Terraform state.

## Object Lock (audit bucket)

Object Lock is enabled at creation (`object_lock_enabled = true`, which forces
versioning on). The default retention uses **COMPLIANCE** mode for
`audit_retention_years` years — even the account root cannot delete or shorten
retention before it expires. Choose `audit_retention_years` carefully; it can
be raised but not lowered for already-locked objects.

## Inputs

| Name                    | Type          | Default | Description                                                            |
| ----------------------- | ------------- | ------- | ---------------------------------------------------------------------- |
| `name_prefix`           | `string`      | —       | Resource name prefix, e.g. `autofounder-ai-staging`.                   |
| `kms_key_arn`           | `string`      | `null`  | CMK for SSE-KMS; `null` falls back to SSE-S3.                          |
| `audit_retention_years` | `number`      | `7`     | Object Lock COMPLIANCE retention (years) for the audit bucket.         |
| `force_destroy`         | `bool`        | `false` | Allow deleting non-empty buckets on destroy (keep `false` in prod).    |
| `tags`                  | `map(string)` | `{}`    | Extra tags (platform tags come from provider `default_tags`).          |

## Outputs

| Name              | Description                                            |
| ----------------- | ------------------------------------------------------ |
| `bucket_ids`      | Map `purpose -> bucket id`, including `audit`.          |
| `bucket_arns`     | Map `purpose -> bucket ARN`, including `audit`.         |
| `audit_bucket_id` | Id of the Object-Lock audit bucket.                    |

## Usage

```hcl
module "s3" {
  source      = "./modules/s3"
  name_prefix = "autofounder-ai-staging"
  kms_key_arn = module.secrets.kms_key_arn # null -> SSE-S3
}
```
