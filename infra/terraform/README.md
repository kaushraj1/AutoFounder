# AutoFounder AI — Infrastructure (Terraform)

Infrastructure-as-code for the AutoFounder AI platform on AWS (region **ap-south-1**).
This is the root composition; reusable building blocks live under [`modules/`](modules/).

> **Status:** ✅ delivered — `AF-012` networking, `AF-019` iam, `AF-020` secrets (per-env),
> and `AF-021` ecr (in the [`global/`](global/) stack). ⏳ pending — `AF-013` ecs,
> `AF-015` elasticache, `AF-016` s3, `AF-017` messaging, `AF-018` alb
> (add their `module` blocks to [`main.tf`](main.tf) as they land).
>
> **Two stacks:** this directory is the **per-environment** stack (one state per
> env: networking, iam, secrets, + future ecs/alb/cache). [`global/`](global/) is
> the **account-global** stack (one shared state: ECR, since images are promoted
> staging→prod by digest). Bootstrap each state target once:
> `./scripts/bootstrap-state.sh {staging|production|global}`.

> ⚠️ **Naming collision to resolve before `AF-013`:** the existing CD workflows
> (`.github/workflows/deploy-{staging,prod}.yml`) hardcode `autofounderai-cluster`,
> `autofounderai-backend`, and ECR `autofounderai/backend` (**no hyphen**), while
> this IaC uses the spec-correct `autofounder-ai` prefix. `AF-013`'s
> Terraform-created cluster will be `autofounder-ai-{env}-cluster`, which the deploy
> workflows won't match. Converge on `autofounder-ai` and drive the workflow names
> from Terraform outputs/secrets (e.g. `ECS_CLUSTER`) when `AF-013` lands.

## Layout

```
infra/terraform/
├── backend.tf          # S3 remote state + DynamoDB lock (partial config)
├── providers.tf        # AWS provider + default_tags (the 4 platform tags)
├── versions.tf         # Terraform >= 1.6, AWS provider ~> 5.0
├── variables.tf        # root inputs
├── locals.tf           # name_prefix + common_tags
├── main.tf             # module wiring (networking; more added per task)
├── outputs.tf          # passthrough of network outputs for downstream modules
├── env/
│   ├── staging.tfvars          # staging inputs (2 AZ, single NAT)
│   ├── production.tfvars       # production inputs (3 AZ, NAT per AZ)
│   ├── staging.backend.hcl     # staging state bucket + key
│   └── production.backend.hcl  # production state bucket + key
├── scripts/
│   ├── bootstrap-state.sh      # create state bucket + lock table (Linux/macOS)
│   └── bootstrap-state.ps1     # create state bucket + lock table (Windows)
├── modules/
│   ├── networking/             # AF-012: VPC, subnets, NAT, VPC endpoints, flow logs
│   ├── secrets/                # AF-020: KMS CMK + Secrets Manager containers
│   ├── iam/                    # AF-019: ECS task execution + per-service task roles
│   └── ecr/                    # AF-021: ECR repositories (consumed by global/)
└── global/                     # account-global stack (own state): ECR
    ├── main.tf  backend.tf  providers.tf  variables.tf  locals.tf  outputs.tf  versions.tf
    └── global.backend.hcl      # global state bucket + key
```

## Prerequisites

- Terraform `>= 1.6`, AWS CLI v2.
- AWS credentials for the target account (env vars, SSO, or OIDC in CI).
- **One-time per environment:** create the remote-state backend (bucket + lock table):

  ```bash
  # Linux/macOS
  ./scripts/bootstrap-state.sh staging
  # Windows
  ./scripts/bootstrap-state.ps1 -Environment staging
  ```

## Usage

```bash
cd infra/terraform

# Staging
terraform init -backend-config=env/staging.backend.hcl
terraform fmt -check -recursive
terraform validate
terraform plan  -var-file=env/staging.tfvars      # attach output to the PR
terraform apply -var-file=env/staging.tfvars

# Production (separate state — re-init against the prod backend)
terraform init -reconfigure -backend-config=env/production.backend.hcl
terraform plan  -var-file=env/production.tfvars
terraform apply -var-file=env/production.tfvars
```

> CI (`.github/workflows/terraform-validate.yml`) runs `fmt -check` + `validate`
> on every PR touching `infra/terraform/**`. `plan`/`apply` require AWS credentials
> and are run by an operator (or the deploy pipeline) — never with hardcoded keys.

## Conventions

- **Naming:** `${project}-${environment}-<resource>` → e.g. `autofounder-ai-staging-vpc`.
- **Tags:** every resource carries `env`, `project`, `managed-by`, `team`
  (applied via provider `default_tags`).
- **State:** per-environment S3 bucket, shared DynamoDB lock table, encrypted,
  versioned, 90-day non-current version retention.
- **IAM:** least-privilege; no `*:*`. (CI for this is part of `AF-019`/`AF-022`.)

## What `AF-012` provisions

A multi-AZ VPC with public + private subnets, NAT gateways (single in staging,
one-per-AZ in production), an S3 **gateway** endpoint, and **interface** endpoints
for ECR (`api` + `dkr`) and Secrets Manager — so ECS Fargate can pull images and
read secrets without internet egress. VPC Flow Logs stream to CloudWatch.
See [`modules/networking/README.md`](modules/networking/README.md).
