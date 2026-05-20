# Deployment Spec — AutoFounder AI

> GCP infrastructure, Cloud Run services, Terraform workflow,
> environment strategy, and release process.

---

## Environment Strategy

| Environment | Purpose | Lifetime | Trigger |
|-------------|---------|----------|---------|
| `local` | Developer laptop via Docker Compose | ephemeral | `make stack` |
| `dev` | Shared integration environment, latest `development` branch | persistent | Push to `development` |
| `staging` | Pre-production, mirrors prod config exactly | persistent | Push to `testing` |
| `production` | Live, customer-facing | persistent | PR merge to `main` + manual approval |

### Parity rules

- `staging` and `production` run identical container images (same digest) — only environment
  variables differ.
- `dev` may run a lightweight image variant (no multi-replica, cheaper Cloud SQL tier).
- `local` uses Docker Compose with Postgres 16 + Redis 7 — same major versions as Cloud SQL
  and Memorystore in production.
- No production data ever reaches `dev` or `local`. Test data is seeded via `make seed`.

---

## GCP Project Structure

```
autofounder-ai-dev         # dev environment
autofounder-ai-staging     # staging environment
autofounder-ai-prod        # production environment
autofounder-ai-shared      # shared: Artifact Registry, Secret Manager, CI service accounts
```

One GCP project per environment prevents a misconfigured staging deploy from touching prod
resources. The `shared` project holds the container registry and CI/CD identities used across all
environments.

---

## Compute — Cloud Run Services

| Service | Source | Port | Min instances | Concurrency |
|---------|--------|------|---------------|-------------|
| `api` | `backend/` | 8000 | 1 (prod) / 0 (dev) | 80 |
| `orchestrator` | `backend/` | 8001 | 1 | 10 |
| `ai-services` | `backend/` | 8002 | 0 | 5 |
| `frontend-web` | `frontend-web/` | 3000 | 1 | 80 |

**Gateway**: Cloud Load Balancing with HTTPS → Cloud Run services via serverless NEGs.
**Domain**: `api.autofounder.ai`, `app.autofounder.ai` managed by Cloud DNS + Google-managed SSL cert.

### Why Cloud Run over GKE

- No cluster management, node pool sizing, or control-plane upgrades.
- Scale to zero for `ai-services` and `orchestrator` (agent steps are bursty, not continuous).
- gRPC support via HTTP/2 on Cloud Run (internal traffic via VPC connector).
- Spot/preemptible pricing for batch agent workloads via Cloud Run Jobs.

### Agent sandbox execution

Long-running build tasks (Pillar 3 code gen, Pillar 4 test execution) run as **Cloud Run Jobs**:
- One-off invocation per agent step.
- Sandboxed: no external network access except explicit allow-list via VPC firewall rules.
- 15-minute max execution timeout (configurable per pillar SLA).
- Ephemeral: job container is destroyed on completion. Artifacts written to GCS.

---

## Managed Services

| Concern | GCP Service | Notes |
|---------|-------------|-------|
| Relational DB | Cloud SQL (PostgreSQL 16) | HA replica, automatic backups, PITR |
| Cache | Memorystore for Redis | Standard tier, 4 GB (prod), 1 GB (dev) |
| Object storage | Cloud Storage | Artifacts, RLHF data lake, Terraform state |
| Message queue | Pub/Sub | Agent event bus, push-notification pipeline |
| Container registry | Artifact Registry | `{region}-docker.pkg.dev/{shared_project}/autofounder-ai/` |
| Secrets | Secret Manager | One secret per credential, versioned |
| DNS | Cloud DNS | `autofounder.ai` zone |
| TLS | Google-managed SSL | Auto-renewed, attached to load balancer |
| Monitoring | Cloud Monitoring + Prometheus | Alert policies on P99 latency, error rate |
| Logging | Cloud Logging | Fluent Bit sidecar, structured JSON |
| Tracing | Cloud Trace + OTel | W3C traceparent end-to-end |
| Functions | Cloud Functions (2nd gen) | FCM push notification sender, webhook forwarders |

---

## Terraform Workflow

### Repository layout

```
infra/
├── modules/
│   ├── networking/        VPC, subnets, VPC connector, firewall rules
│   ├── cloud-run/         Service definitions, IAM bindings
│   ├── cloud-sql/         PostgreSQL instance, databases, users
│   ├── memorystore/       Redis instance
│   ├── cloud-storage/     Buckets, lifecycle rules, IAM
│   ├── pubsub/            Topics, subscriptions, IAM
│   ├── secret-manager/    Secret placeholders (values set out-of-band)
│   ├── artifact-registry/ Repositories, IAM
│   └── iam/               Service accounts, roles, workload identity
├── env/
│   ├── dev/               main.tf, variables.tf, terraform.tfvars
│   ├── staging/           main.tf, variables.tf, terraform.tfvars
│   └── production/        main.tf, variables.tf, terraform.tfvars
└── backend.tf             GCS backend config (per env)
```

### State backend

```hcl
terraform {
  backend "gcs" {
    bucket = "autofounder-ai-tfstate-{env}"
    prefix = "terraform/state"
  }
}
```

Bucket has versioning enabled and object retention set to 90 days.

### Workflow for infra changes

```
1. Branch: feature/AF-XXX-terraform-description
2. Edit module under infra/modules/ or infra/env/{env}/
3. terraform fmt && terraform validate
4. terraform plan -var-file=env/{env}/terraform.tfvars  → attach output to PR
5. PR review — at least one approval required for prod changes
6. Merge to development → CI applies to dev automatically
7. Merge to testing → CI applies to staging automatically
8. Merge to main → CI applies to production after manual approval gate
```

### Naming convention for resources

```
{service}-{env}-{region_short}
e.g.:
  api-prod-as1          (Cloud Run service, production, asia-south1)
  pg-staging-as1        (Cloud SQL instance, staging)
  redis-dev-as1         (Memorystore, dev)
```

### Required tags on every resource

```hcl
labels = {
  env        = var.environment          # dev | staging | production
  project    = "autofounder-ai"
  managed-by = "terraform"
  team       = "platform"
}
```

---

## CI/CD Pipeline

### GitHub Actions → GCP Cloud Deploy

```
PR opened / updated
  ├── make quality              (lint + typecheck — all workspaces)
  ├── uv run pytest             (backend unit + integration tests)
  ├── pnpm test                 (frontend unit tests)
  ├── trivy fs .                (container + dependency vulnerability scan)
  ├── semgrep --config auto .   (SAST)
  └── gitleaks detect           (secret scan)

Merge to development
  ├── docker build + push → Artifact Registry (dev tag)
  └── gcloud run deploy → autofounder-ai-dev project

Merge to testing
  ├── docker build + push → Artifact Registry (staging tag)
  └── Cloud Deploy → staging environment (requires passing integration test suite)

Merge to main  (requires PR approval + all CI gates green)
  ├── docker build + push → Artifact Registry (immutable sha tag + latest-prod tag)
  ├── Cloud Deploy → production environment
  │     ├── Canary: 10% traffic → new revision
  │     ├── Wait 5 min, check error rate < 1%
  │     └── Promote to 100% — or auto-rollback on breach
  └── Notify team via Slack
```

### Docker image tags

| Tag | Meaning |
|-----|---------|
| `sha-{git_sha}` | Immutable, used for prod deploys |
| `dev-latest` | Latest build from `development` branch |
| `staging-latest` | Latest build from `testing` branch |

---

## Rollback

### Automatic (canary breach)

Cloud Run revision traffic is split. On error rate > 1% during canary, Cloud Deploy automatically
routes 100% back to the previous revision. No human intervention needed.

### Manual

```bash
# List revisions
gcloud run revisions list --service api --region asia-south1 --project autofounder-ai-prod

# Roll back to specific revision
gcloud run services update-traffic api \
  --to-revisions api-00042-xyz=100 \
  --region asia-south1 \
  --project autofounder-ai-prod
```

Database migrations are not automatically rolled down on rollback. A matching Alembic
`downgrade` must be run manually if the new schema is incompatible with the rolled-back code.
Design migrations to be backward-compatible (additive-only) to avoid this.

---

## Secrets Management

Secrets are injected into Cloud Run at deploy time via Secret Manager volume mounts or
environment variable bindings — never baked into container images.

```hcl
# In Cloud Run service Terraform config
env {
  name = "STRIPE_SECRET_KEY"
  value_source {
    secret_key_ref {
      secret  = "autofounder-ai-prod-stripe-secret-key"
      version = "latest"
    }
  }
}
```

Secret rotation: update the secret version in Secret Manager, then redeploy the Cloud Run
service to pick up the new version (Cloud Run does not hot-reload secrets).

---

## Local Development Reference

```bash
make install      # pnpm install + uv sync
make stack        # docker compose up -d  (Postgres 16 + Redis 7)
make dev          # pnpm dev  →  turbo dev (frontend-web + mobile)

# Backend only
cd backend && uv run uvicorn autofounder_ai.main:app --reload --port 8000

# Apply DB migrations locally
cd backend && uv run alembic upgrade head

# Seed test data
cd backend && uv run python -m autofounder_ai.scripts.seed
```
