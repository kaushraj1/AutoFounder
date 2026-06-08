# networking module (AF-012)

Multi-AZ VPC foundation for the AutoFounder AI platform: VPC, public/private
subnets, NAT gateways, internet gateway, route tables, VPC endpoints, and VPC
Flow Logs. Every other infra module (ecs, alb, elasticache, s3 access, messaging)
consumes this module's outputs.

## What it creates

| Resource | Notes |
|---|---|
| VPC | DNS support + hostnames enabled |
| Public subnets (1/AZ) | ALB + NAT gateways; auto-assign public IP |
| Private subnets (1/AZ) | ECS Fargate tasks, ElastiCache, interface endpoints |
| Internet gateway | egress for public subnets |
| NAT gateway(s) | `single_nat_gateway=true` → 1 shared; `false` → one per AZ (HA) |
| Route tables | 1 public (shared) + 1 private per AZ (each → its AZ's NAT) |
| S3 gateway endpoint | attached to private route tables (free; cuts NAT cost) |
| Interface endpoints | ECR `api` + `dkr`, Secrets Manager (HTTPS-only SG, private DNS) |
| VPC Flow Logs | → CloudWatch Logs, least-privilege IAM role (toggle via `enable_flow_logs`) |

Subnet CIDRs are derived with `cidrsubnet(vpc_cidr, 4, n)` (=> /20 subnets from a
/16 VPC), reserving blocks 0–2 for public and 3–5 for private, so adding an AZ
never renumbers existing subnets.

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `name_prefix` | string | — | Resource name prefix, e.g. `autofounder-ai-staging` (lowercase/digits/hyphens). |
| `vpc_cidr` | string | — | VPC IPv4 CIDR (use a `/16`). |
| `az_count` | number | `2` | AZs to span (2 or 3). |
| `single_nat_gateway` | bool | `false` | One shared NAT (cheap/staging) vs one per AZ (HA/prod). |
| `interface_endpoint_services` | list(string) | `["ecr.api","ecr.dkr","secretsmanager"]` | Interface endpoint short service names (region prefixed automatically). |
| `enable_flow_logs` | bool | `true` | Send VPC Flow Logs to CloudWatch. |
| `flow_logs_retention_days` | number | `30` | Flow log retention. |
| `tags` | map(string) | `{}` | Extra tags (the 4 platform tags come from provider `default_tags`). |

## Outputs

`vpc_id`, `vpc_cidr_block`, `availability_zones`, `public_subnet_ids`,
`private_subnet_ids`, `public_route_table_id`, `private_route_table_ids`,
`nat_gateway_ids`, `nat_public_ips`, `internet_gateway_id`,
`vpc_endpoint_security_group_id`, `s3_gateway_endpoint_id`, `interface_endpoint_ids`.

## Design notes

- **No bastion host.** Operator/agent access to private subnets should use AWS
  **SSM Session Manager** (no open SSH port, IAM-audited) rather than a bastion EC2.
  Add one in a later task only if a hard requirement appears.
- **Adding endpoints:** ECS tasks that ship logs/use SSM/KMS typically also want
  `logs`, `ssm`, `kms`, `sts` interface endpoints — append them to
  `interface_endpoint_services` when those modules land.
- **Egress allow-lists:** use `nat_public_ips` as the stable source IPs for any
  third-party service that allow-lists by IP.
