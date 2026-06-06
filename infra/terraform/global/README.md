# Global stack (account-wide infrastructure)

Resources that are shared by **every** environment and must exist exactly once
per AWS account live here, in their own Terraform state — separate from the
per-environment stack in [`../`](../).

> **Why a separate stack?** `deployment.md` requires that staging and production
> run the **identical container image (same ECR digest)** — an image built once
> is promoted by digest. That mandates a single shared ECR repository per service,
> which cannot live in a per-environment state (it would be created twice and
> collide). Account-global resources therefore get their own state.

## Contents

| Resource | Task | Notes |
|---|---|---|
| ECR repositories | `AF-021` | one repo per service (`autofounder-ai/backend`, `autofounder-ai/web`), scan-on-push, lifecycle policy |
| _(future)_ GitHub OIDC provider + CI deploy role | `AF-022` | added here when CD is wired |

## Usage

```bash
cd infra/terraform/global

# One-time: create the global state bucket (+ shared lock table)
../scripts/bootstrap-state.sh global        # or .ps1 -Environment global

terraform init -backend-config=global.backend.hcl
terraform fmt -check -recursive
terraform validate
terraform plan      # no -var-file needed; sensible defaults
terraform apply
```

State: `s3://autofounder-ai-tfstate-global/global/terraform.tfstate`.

The per-environment IAM module references these ECR repositories by **constructed
ARN** (account + region + `autofounder-ai/<service>`), so there is no Terraform
state coupling between the global and per-env stacks.
