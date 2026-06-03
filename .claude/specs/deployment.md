# Deployment Spec — AutoFounder AI

> AWS ECS Fargate infrastructure, Terraform workflow,
> environment strategy, CI/CD pipeline, and release process.
>
> **Authoritative source**: `CLAUDE.md §17, §18, §27`

---

## Environment Strategy

| Environment | Purpose | Lifetime | Trigger |
|-------------|---------|----------|---------|
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
| `backend` | `backend/` | 8000 | 2 (multi-AZ) | 1024 / 2048 |
| `web` | `frontend/` | 3000 | 2 (multi-AZ) | 512 / 1024 |

> **Phase 1 (consolidated backend):** the API gateway, LangGraph orchestrator, and agent workers
> ship as internal modules of one `backend` service
> (`backend/app/{api,orchestrator,workers}`). They are split into dedicated
> `orchestrator` / `ai-services` ECS services in Phase 4 if scale requires.

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
- SQS queue depth (agent worker tasks inside the backend)

---

## Terraform Workflow

### Repository layout

```
infra/
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
```

### State backend

```hcl
terraform {
  backend "s3" {
    bucket         = "autofounder-ai-tfstate-${var.environment}"
    key            = "terraform/state"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "autofounder-ai-tfstate-lock"
  }
}
```

Bucket has versioning enabled and a 90-day object version retention lifecycle policy.

### Workflow for infra changes

```
1. Branch: feature/AF-XXX-terraform-description
2. Edit module under infra/terraform/modules/ or infra/terraform/env/
3. terraform fmt && terraform validate
4. terraform plan -var-file=env/staging.tfvars  → attach output to PR
5. PR review — at least one approval required for production changes
6. Merge to testing  → CI applies to staging automatically
7. Merge to main     → CI applies to production after manual approval gate
```

### Required tags on every resource

```hcl
tags = {
  env        = var.environment          # staging | production
  project    = "autofounder-ai"
  managed-by = "terraform"
  team       = "platform"
}
```

---

## CI/CD Pipeline

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

### Docker image tags

| Tag | Meaning |
|-----|---------|
| `sha-{git_sha}` | Immutable; used for all prod deploys |
| `staging-latest` | Latest build from `testing` branch |
| `prod-latest` | Latest promoted production image |

---

## Rollback

### Automatic (canary breach)

AWS CodeDeploy monitors the canary. On error rate > 1%, CodeDeploy automatically routes 100%
traffic back to the original task set. No human intervention needed.

### Manual

```bash
# Stop in-progress deployment and trigger automatic rollback
aws deploy stop-deployment \
  --deployment-id d-XXXXXXXXX \
  --auto-rollback-enabled \
  --region ap-south-1

# Or directly update service to previous task definition revision
aws ecs update-service \
  --cluster autofounder-ai-prod \
  --service backend \
  --task-definition backend:PREVIOUS_REVISION \
  --region ap-south-1
```

Database migrations are not automatically rolled back. A matching Alembic `downgrade` must be
run manually if the new schema is incompatible with the rolled-back code.
**Design all migrations to be additive-only** to avoid this.

---

## Secrets Management

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

---

## Local Development Reference

```bash
# Install all dependencies
make install          # pnpm install + uv sync --all-groups

# Start Supabase (PostgreSQL + pgvector + Auth + Storage + Realtime)
supabase start

# Start Redis only
make stack            # docker compose up -d

# Run the consolidated backend (API + orchestrator + agent workers)
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Run frontend
pnpm --filter @autofounder-ai/frontend dev   # Next.js Founder Portal (+ /admin route group)  :3000

# Apply DB migrations
cd backend && uv run alembic upgrade head

# Quality gate (run before every PR)
make quality          # backend ruff + mypy + pytest, then JS lint

# Infra plan
cd infra/terraform && terraform plan -var-file=env/staging.tfvars
```
