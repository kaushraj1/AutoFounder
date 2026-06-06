# elasticache module (AF-015)

Redis 7 cache for the AutoFounder AI platform: a single ElastiCache replication
group (cluster-mode disabled — one primary + read replicas) deployed Multi-AZ
across the networking module's private subnets, encrypted at rest and in transit,
and reachable only from inside the VPC on port 6379. Consumes `vpc_id`,
`private_subnet_ids`, and `vpc_cidr` from the networking module and (optionally)
`kms_key_arn` from the secrets module.

## What it creates

| Resource | Notes |
|---|---|
| Cache subnet group | spans `private_subnet_ids` (private subnets only) |
| Security group | ingress 6379 from `vpc_cidr` only; egress to the VPC |
| Redis replication group | cluster-mode disabled: 1 primary + `num_cache_clusters - 1` replicas |

Multi-AZ + automatic failover are enabled by default and require
`num_cache_clusters >= 2`. Encryption at rest uses the platform CMK when
`kms_key_arn` is supplied, otherwise the AWS-managed key.

## Security & secrets

- **No secret in state.** `auth_token` is optional and supplied out-of-band
  (e.g. from Secrets Manager); this module never generates a `random_password`
  and never persists a token value. When set, it requires
  `transit_encryption_enabled = true` (TLS in transit).
- **Network isolation.** Redis accepts traffic only from `vpc_cidr` on 6379 —
  it is never exposed publicly.
- **Encryption.** At-rest and in-transit encryption are on by default.

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `name_prefix` | string | — | Resource name prefix, e.g. `autofounder-ai-staging`. |
| `vpc_id` | string | — | VPC for the cluster and its SG (networking module). |
| `private_subnet_ids` | list(string) | — | Private subnets for the cache subnet group. |
| `vpc_cidr` | string | — | Only CIDR allowed to reach Redis on 6379. |
| `node_type` | string | `cache.t4g.micro` | Node instance type. |
| `num_cache_clusters` | number | `2` | Total nodes (1 primary + N-1 replicas). |
| `engine_version` | string | `7.1` | Redis engine version. |
| `multi_az_enabled` | bool | `true` | Replicas in different AZs from the primary. |
| `automatic_failover_enabled` | bool | `true` | Auto-promote a replica on primary failure. |
| `transit_encryption_enabled` | bool | `true` | TLS in transit (required for `auth_token`). |
| `at_rest_encryption_enabled` | bool | `true` | Encryption at rest. |
| `kms_key_arn` | string | `null` | CMK for at-rest encryption; null => AWS-managed key. |
| `auth_token` | string (sensitive) | `null` | Optional out-of-band Redis AUTH token. |
| `snapshot_retention_limit` | number | `5` | Days to retain automatic snapshots (0 disables). |
| `tags` | map(string) | `{}` | Extra tags (the 4 platform tags come from provider `default_tags`). |

## Outputs

`primary_endpoint_address`, `reader_endpoint_address`, `port`,
`security_group_id`, `replication_group_id`.

## Design notes

- **Cluster-mode disabled** suits a SaaS cache/session/rate-limit workload: one
  write endpoint (`primary_endpoint_address`) plus a fan-out read endpoint
  (`reader_endpoint_address`). Switch to cluster-mode-enabled only if a single
  shard's memory/throughput becomes the bottleneck.
- **`apply_immediately = false`** so engine/version changes land in the next
  maintenance window rather than disrupting live traffic; flip it deliberately
  for an emergency change.
- **AUTH token rotation:** store the token in Secrets Manager, pass it in via
  `auth_token`, and rotate by updating the secret then re-applying — the value
  never enters Terraform state from this module.
