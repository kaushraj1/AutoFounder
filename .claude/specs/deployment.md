# Deployment Spec — AutoFounder AI

<<<<<<< HEAD
> GCP infrastructure, Cloud Run services, Terraform workflow,
> environment strategy, and release process.
=======
> AWS ECS Fargate infrastructure, Terraform workflow,
> environment strategy, CI/CD pipeline, and release process.
>
> **Authoritative source**: `CLAUDE.md §17, §18, §27`
>>>>>>> dev

---

## Environment Strategy

| Environment | Purpose | Lifetime | Trigger |
|-------------|---------|----------|---------|
<<<<<<< HEAD
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
=======
| `sandbox` | Ephemeral Fargate task (Firecracker/gVisor) — build/test of generated MVPs | minutes | Agent pipeline (Pillar 3 / 4) |
| `staging` | Mirrors prod config exactly | persistent | Push to `testing` branch |
| `production` | ECS Fargate, multi-AZ, blue/green | persistent | PR merge to `main` + manual approval |

### Parity rules

- `staging` and `production` run identical container images (same ECR digest) — only env vars differ.
- `sandbox` is ephemeral, isolated network, zero shared state with prod.
- Local dev uses Supabase CLI (`supabase start`) for DB/Auth/Storage/Realtime + Docker Compose for Redis only.
- No production data ever reaches `staging` or local. Test data seeded via `make seed`.

---

## AWS Services

| Concern | Service |
|---------|---------|
| DNS | Amazon Route 53 |
| Edge / CDN | Amazon CloudFront |
| WAF / DDoS | AWS WAF + AWS Shield |
| Load Balancing | Application Load Balancer (L7) |
| Compute | **Amazon ECS on Fargate** (multi-AZ, private subnets) |
| Cache | Amazon ElastiCache for Redis 7 |
| Object Storage | **Supabase Storage** (app artifacts, assets) + Amazon S3 (data lake, audit logs, RLHF datasets — 7-yr S3 Object Lock) |
| Container Registry | Amazon ECR (image scanning on push, lifecycle policies) |
| Secrets | AWS Secrets Manager + SSM Parameter Store (KMS-encrypted) |
| IAM | AWS IAM (least-privilege; no `*:*`) |
| Encryption | AWS KMS |
| Backups | AWS Backup |
| Compliance | AWS Config |
| Async Bus | Amazon SQS (per-pillar queues + DLQs), SNS (fan-out / notifications), EventBridge (schema registry, cross-service routing) |
| Primary Message Bus | **Confluent Kafka** (inter-agent events + LLMOps telemetry) |
| Long-running workflows | AWS Step Functions |
| Logs | Amazon CloudWatch + CloudTrail (audit) |
| Tracing | AWS X-Ray (+ OTel exporters) |
| Networking | VPC, NAT Gateway, Bastion Host, VPC Endpoints (S3 / ECR / Secrets Manager) |
| Deploy | AWS CodeDeploy (ECS blue/green) |

> **Note**: Relational DB + pgvector + Auth + Storage + Realtime handled by **Supabase** (hosted).
> No RDS or self-managed PostgreSQL.

---

## ECS Fargate Services

| Service | Source | Port | Min tasks (prod) | CPU / RAM |
|---------|--------|------|-----------------|-----------|
| `api` | `apps/api/` | 8000 | 2 (multi-AZ) | 512 / 1024 |
| `orchestrator` | `apps/orchestrator/` | 8001 | 1 | 1024 / 2048 |
| `ai-services` | `apps/ai-services/` | 8002 | 1 | 2048 / 4096 |
| `web` | `apps/web/` | 3000 | 2 (multi-AZ) | 512 / 1024 |
| `admin` | `apps/admin/` | 3001 | 1 | 256 / 512 |

**Gateway**: ALB (L7) → HTTPS listeners → target groups per ECS service.
**Domain**: `api.autofounder.ai`, `app.autofounder.ai` via Route 53 + ACM.

### Agent sandbox execution

Long-running build tasks (Pillar 3 code gen, Pillar 4 test execution) run as **ephemeral Fargate tasks**:

- One-off invocation per agent step via ECS `run_task` API.
- Isolation: Firecracker / gVisor; strict egress allow-list only (no arbitrary outbound).
- Max execution: 15 min (configurable per pillar SLA). Spin-up SLA: < 10 s.
- Ephemeral: task terminates on completion. Artifacts written to Supabase Storage.

### Auto Scaling

ECS Service Auto Scaling — target tracking on:
- CPU utilisation (target 70%)
- RPS per target (ALB metric)
- SQS queue depth (for `ai-services`)
>>>>>>> dev

---

## Terraform Workflow

### Repository layout

```
infra/
<<<<<<< HEAD
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
=======
├── terraform/
│   ├── modules/
│   │   ├── networking/      VPC, public/private subnets (Multi-AZ), NAT gateways, VPC endpoints
│   │   ├── ecs/             Fargate cluster, task definitions per service, auto-scaling policies
│   │   ├── alb/             ALB + HTTPS listener + target groups; CloudFront + WAF + Shield
│   │   ├── elasticache/     Redis 7 cluster (Multi-AZ), subnet groups, auth token
│   │   ├── s3/              Artifacts bucket, RLHF data lake, prompt-templates; Object Lock on audit bucket (7 yr)
│   │   ├── messaging/       Confluent Kafka cluster, EventBridge bus + rules, per-pillar SQS queues + DLQs, SNS topic
│   │   ├── ecr/             ECR repo per service, image scanning on push, lifecycle policies
│   │   ├── secrets/         Secrets Manager entries + SSM hierarchy; KMS CMK for at-rest encryption
│   │   ├── iam/             Least-privilege task execution roles per service; no `*:*`
│   │   └── codedeploy/      Blue/green deployment groups per ECS service
│   └── env/
│       ├── staging.tfvars
│       └── production.tfvars
└── codedeploy/
    ├── appspec.yml
    └── scripts/
>>>>>>> dev
```

### State backend

```hcl
terraform {
<<<<<<< HEAD
  backend "gcs" {
    bucket = "autofounder-ai-tfstate-{env}"
    prefix = "terraform/state"
=======
  backend "s3" {
    bucket         = "autofounder-ai-tfstate-${var.environment}"
    key            = "terraform/state"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "autofounder-ai-tfstate-lock"
>>>>>>> dev
  }
}
```

<<<<<<< HEAD
Bucket has versioning enabled and object retention set to 90 days.
=======
Bucket has versioning enabled and a 90-day object version retention lifecycle policy.
>>>>>>> dev

### Workflow for infra changes

```
1. Branch: feature/AF-XXX-terraform-description
<<<<<<< HEAD
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
=======
2. Edit module under infra/terraform/modules/ or infra/terraform/env/
3. terraform fmt && terraform validate
4. terraform plan -var-file=env/staging.tfvars  → attach output to PR
5. PR review — at least one approval required for production changes
6. Merge to testing  → CI applies to staging automatically
7. Merge to main     → CI applies to production after manual approval gate
>>>>>>> dev
```

### Required tags on every resource

```hcl
<<<<<<< HEAD
labels = {
  env        = var.environment          # dev | staging | production
=======
tags = {
  env        = var.environment          # staging | production
>>>>>>> dev
  project    = "autofounder-ai"
  managed-by = "terraform"
  team       = "platform"
}
```

---

## CI/CD Pipeline

<<<<<<< HEAD
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

=======
```
PR opened / updated
  ├── lint          (ruff, eslint, prettier)
  ├── typecheck     (mypy, tsc strict)
  ├── unit tests    (pytest, jest)
  ├── integration   (Playwright, testcontainers)
  ├── security scan (Trivy, Semgrep, Snyk, Gitleaks)
  ├── LLM-as-judge eval (LangSmith — must meet threshold)
  └── build images → push to ECR (sha-{git_sha} tag)

Merge to testing
  ├── docker build + push → ECR (staging-latest)
  └── AWS CodeDeploy → ECS staging (blue/green)

Merge to main  (requires PR approval + all CI gates green)
  ├── docker build + push → ECR (sha-{git_sha} + prod-latest)
  ├── AWS CodeDeploy → ECS production (blue/green)
  │     ├── Deploy new task set (blue)
  │     ├── Canary: 10% traffic → new task set
  │     ├── Smoke test
  │     ├── Wait 5 min — error rate < 1%
  │     └── Ramp to 100% — or auto-rollback on breach
  └── Notify team (SNS → Slack)
```

PR gates that **must pass**: lint, typecheck, unit, integration, security, LLM-judge ≥ threshold.
No direct push to `main`.

>>>>>>> dev
### Docker image tags

| Tag | Meaning |
|-----|---------|
<<<<<<< HEAD
| `sha-{git_sha}` | Immutable, used for prod deploys |
| `dev-latest` | Latest build from `development` branch |
| `staging-latest` | Latest build from `testing` branch |
=======
| `sha-{git_sha}` | Immutable; used for all prod deploys |
| `staging-latest` | Latest build from `testing` branch |
| `prod-latest` | Latest promoted production image |
>>>>>>> dev

---

## Rollback

### Automatic (canary breach)

<<<<<<< HEAD
Cloud Run revision traffic is split. On error rate > 1% during canary, Cloud Deploy automatically
routes 100% back to the previous revision. No human intervention needed.
=======
AWS CodeDeploy monitors the canary. On error rate > 1%, CodeDeploy automatically routes 100%
traffic back to the original task set. No human intervention needed.
>>>>>>> dev

### Manual

```bash
<<<<<<< HEAD
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
=======
# Stop in-progress deployment and trigger automatic rollback
aws deploy stop-deployment \
  --deployment-id d-XXXXXXXXX \
  --auto-rollback-enabled \
  --region ap-south-1

# Or directly update service to previous task definition revision
aws ecs update-service \
  --cluster autofounder-ai-prod \
  --service api \
  --task-definition api:PREVIOUS_REVISION \
  --region ap-south-1
```

Database migrations are not automatically rolled back. A matching Alembic `downgrade` must be
run manually if the new schema is incompatible with the rolled-back code.
**Design all migrations to be additive-only** to avoid this.
>>>>>>> dev

---

## Secrets Management

<<<<<<< HEAD
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
=======
Secrets are injected into ECS tasks at runtime via Secrets Manager — **never baked into
container images**, **never in `.env` files committed to the repo**.

```json
// ECS task definition (Terraform-managed)
{
  "secrets": [
    {
      "name": "STRIPE_SECRET_KEY",
      "valueFrom": "arn:aws:secretsmanager:ap-south-1:ACCOUNT:secret:autofounder-ai/prod/stripe/secret_key"
    }
  ]
}
```

Secret naming convention: `autofounder-ai/{env}/{service}/{key}`

```
autofounder-ai/prod/supabase/service_role_key
autofounder-ai/prod/supabase/jwt_secret
autofounder-ai/prod/gemini/api_key
autofounder-ai/prod/stripe/secret_key
autofounder-ai/prod/stripe/webhook_secret
autofounder-ai/prod/langsmith/api_key
autofounder-ai/prod/sentry/dsn_backend
autofounder-ai/prod/sentry/dsn_frontend
autofounder-ai/prod/confluent/bootstrap_servers
autofounder-ai/prod/confluent/api_key
autofounder-ai/staging/...
```

Secret rotation: update secret version in Secrets Manager, then force new ECS task deployment.
ECS tasks do not hot-reload secrets.
>>>>>>> dev

---

## Local Development Reference

```bash
<<<<<<< HEAD
make install      # pnpm install + uv sync
make stack        # docker compose up -d  (Postgres 16 + Redis 7)
make dev          # pnpm dev  →  turbo dev (frontend-web + mobile)

# Backend only
cd backend && uv run uvicorn autofounder_ai.main:app --reload --port 8000

# Apply DB migrations locally
cd backend && uv run alembic upgrade head

# Seed test data
cd backend && uv run python -m autofounder_ai.scripts.seed
=======
# Install all dependencies
make install          # pnpm install + uv sync --all-groups

# Start Supabase (PostgreSQL + pgvector + Auth + Storage + Realtime)
supabase start

# Start Redis only
make stack            # docker compose up -d

# Run backend services
cd apps/api && uv run uvicorn main:app --reload --port 8000
cd apps/orchestrator && python -m orchestrator.main
cd apps/ai-services && uv run uvicorn main:app --reload --port 8001

# Run frontend
pnpm --filter web dev      # Next.js Founder Portal  :3000
pnpm --filter admin dev    # Admin dashboard          :3001

# Apply DB migrations
cd apps/api && uv run alembic upgrade head

# Quality gate (run before every PR)
make quality          # ruff + eslint — must both pass

# Infra plan
cd infra/terraform && terraform plan -var-file=env/staging.tfvars
>>>>>>> dev
```
