# CLAUDE.md — Auto-Founder AI

> This file provides project context, architecture guidance, and conventions for Claude Code agents working on the AutoFounder AI platform. Read this before writing any code, modifying any agent, or making infrastructure changes.

---

## Project Overview

**Auto-Founder AI** is a multi-tenant SaaS platform that turns a single text idea into a fully validated, built, deployed, and marketed software business using autonomous multi-agent AI orchestration.

- **One-line vision**: An autonomous, multi-agent orchestrator that transforms a single text-based idea into a fully validated, production-ready, and marketed software business.
- **Org**: Euron Auto-Founder AI, Bengaluru, Karnataka, India
- **Contact**: product@euron.one

---

## Architecture at a Glance

```
User Idea (text prompt)
       │
       ▼
 NestJS API Gateway (multi-tenant)
       │
       ▼
 LangGraph Orchestrator
  ├── Strategist Agent   → market validation, Lean Canvas
  ├── Architect Agent    → DB schema, OpenAPI spec, stack selection
  ├── Coder Agent        → Next.js + FastAPI code generation (parallel)
  ├── Reviewer Agent     → linting, tests, self-healing loop (max 5 retries)
  ├── DevOps Agent       → Terraform/EKS deploy, DNS, SSL, monitoring
  ├── Marketer Agent     → SEO copy, social launch sequences, brand assets
  └── LLMOps Agent       → RLHF logging, prompt optimization, cost telemetry
       │
       ▼
 PostgreSQL (schema-per-tenant) + Qdrant (vector memory) + Redis (session)
       │
       ▼
 AWS EKS (production) / Docker Sandbox (build-time)
```

---

## Repository Structure (Expected)

```
auto-founder-ai/
├── apps/
│   ├── web/                  # Next.js 14 — Founder Portal UI
│   ├── api/                  # NestJS — API Gateway
│   ├── ai-services/          # Python + FastAPI — Agent services
│   └── admin/                # Super Admin Dashboard
├── packages/
│   ├── agents/               # LangGraph agent definitions
│   │   ├── strategist/
│   │   ├── architect/
│   │   ├── coder/
│   │   ├── reviewer/
│   │   ├── devops/
│   │   ├── marketer/
│   │   └── llmops/
│   ├── shared/               # Shared types, utils, constants
│   └── db/                   # Prisma schema, migrations
├── infra/
│   ├── terraform/            # IaC for AWS (EKS, RDS, S3, etc.)
│   └── helm/                 # Helm charts for EKS deployment
├── .github/
│   └── workflows/            # CI/CD via GitHub Actions
└── CLAUDE.md                 # ← you are here
```

---

## Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router) + React
- **Styling**: Tailwind CSS + shadcn/ui
- **Code Editor**: Monaco Editor (for Code Review Studio)
- **State**: Zustand or React Query

### Backend / API Gateway
- **Runtime**: Node.js + NestJS
- **Real-time**: Go + WebSocket (for agent log streaming)
- **Auth**: OAuth 2.0, SAML 2.0, JWT, MFA via Auth0

### AI / Agent Layer
- **Orchestration**: LangGraph (primary), AutoGen (alternative)
- **LLM Routing**: Claude Sonnet (complex reasoning), GPT-4o-mini (simple CRUD tasks)
- **LLM Providers**: Anthropic (Claude), OpenAI (GPT), Google (Gemini) via AWS Bedrock
- **Memory**:
  - Short-term: Redis (session state for active builds)
  - Long-term: Qdrant (vector DB for patterns + user preferences)
- **Agent comms**: gRPC (inter-agent, low latency)
- **Tracing / Evals**: LangSmith, TruLens, Promptfoo

### Databases
| Role | Primary | Alternative |
|---|---|---|
| Relational | PostgreSQL 16 (schema-per-tenant) | CockroachDB |
| Cache | Redis Cluster | DragonflyDB |
| Search | Elasticsearch | Meilisearch |
| Object Storage | AWS S3 | Cloudflare R2 |
| Message Queue | Apache Kafka | RabbitMQ |

### Infrastructure
- **Compute**: AWS EKS (Kubernetes)
- **IaC**: Terraform + CloudFormation
- **CI/CD**: GitHub Actions → ArgoCD → EKS (zero-downtime rolling deploys)
- **Monitoring**: CloudWatch + Prometheus + Grafana
- **Security scanning**: Trivy (containers), Semgrep (SAST), Bandit (Python)

---

## The 7 Agent Pillars

Each agent follows the same 5-stage autonomous loop:
`Understand → Plan → Execute → Verify → Learn`

### 1. Strategist Agent (Idea Validation)
- **Input**: Raw text idea
- **Output**: 5-page Market Analysis Report + Lean Canvas + Viability Score
- **Tools**: Tavily Search, SerpAPI, Crunchbase, G2, Google Trends, Reddit, HackerNews
- **Key sub-tasks**: TAM/SAM/SOM sizing, competitor discovery, keyword mining, persona generation, bias audit, pivot suggestions
- **SLA**: Complete in < 30 minutes (target: ~5–30 min per sub-task)

### 2. Architect Agent (Tech Stack & Schema Design)
- **Input**: Validated idea + functional requirements
- **Output**: OpenAPI spec, ERD, tech stack recommendation, AWS cost forecast
- **Tools**: Mermaid, Swagger/Postman, AWS Pricing API, dbdiagram.io
- **Key sub-tasks**: DB schema design, API contract generation, auth strategy, microservice boundary analysis, scaling plan

### 3. Coder Agent (Autonomous Code Generation)
- **Input**: Architecture spec + OpenAPI contract
- **Output**: Full-stack repo pushed to GitHub with open PR
- **Tools**: LangGraph, GitHub API (Octokit), Docker, Stripe, Auth0, SendGrid
- **Key sub-tasks**: Parallel frontend (Next.js 14) + backend (FastAPI/NestJS) generation, Stripe integration, admin panel, CI/CD config
- **Code style**: Prettier + ESLint (JS/TS), Black + Ruff (Python); zero linting errors on output

### 4. Reviewer Agent (Testing & Self-Healing)
- **Input**: Generated code
- **Output**: Passing test suite; patched code if errors found
- **Tools**: Jest, pytest, Playwright, Trivy, Semgrep, SonarQube, Docker (ephemeral sandboxes)
- **Self-healing loop**: max 5 retry cycles; escalate to human if unresolved
- **Targets**: 80%+ test coverage, 90%+ auto-fix rate, zero OWASP Top 10 violations
- **Sandbox spin-up SLA**: < 10 seconds

### 5. DevOps Agent (Deployment & Infrastructure)
- **Input**: Tested, containerized code
- **Output**: Live URL with SSL, DNS, monitoring, CI/CD configured
- **Tools**: Terraform, ArgoCD, Helm, kubectl, Route53, Let's Encrypt, CloudWatch
- **Key sub-tasks**: EKS provisioning, RDS + ElastiCache + S3 setup, secrets management (AWS Secrets Manager), blue/green deploy config
- **Deploy SLA**: < 10 minutes end-to-end

### 6. Marketer Agent (GTM & Launch Automation)
- **Input**: Live MVP + brand config
- **Output**: Landing page copy, SEO blog drafts, Product Hunt kit, X/LinkedIn/HN launch posts, email drip sequences
- **Tools**: DALL-E 3/Midjourney (visuals), Buffer/Typefully (scheduling), Ahrefs/Semrush (SEO), Resend/SendGrid (email)
- **Hallucination check**: All marketing copy must be cross-referenced against Architect Agent's actual feature list
- **Approval gate**: "Launch Control Center" — all drafts require founder review before posting

### 7. LLMOps Agent (Growth & Continuous Learning)
- **Input**: User interactions, accept/reject signals, trace logs
- **Output**: Optimized prompts, fine-tuning datasets, model routing rules, cost telemetry
- **Tools**: LangSmith, DSPy, Promptfoo, PostHog, Prometheus, AWS Step Functions
- **Key sub-tasks**: RLHF data prep, prompt A/B testing, hallucination tracking, drift detection, per-user cost telemetry
- **Cadence**: Weekly fine-tuning / prompt optimization pipeline

---

## Multi-Tenancy Rules

- **Database**: Schema-per-tenant isolation in PostgreSQL. Never share schemas between tenants.
- **Storage**: All S3 paths must be prefixed with `tenant_id/`.
- **Compute**: Agent worker pods are tenant-scoped; no shared state between tenant builds.
- **Auth**: All API routes must validate `tenant_id` from the JWT claims before any DB query.
- **Data deletion**: Implement GDPR "Right to Erasure" — full tenant data wipe must be available on request, including generated IP stored in S3.

---

## Security & Compliance Requirements

- **Encryption**: AES-256 at rest, TLS 1.3 in transit — mandatory everywhere.
- **Auth**: OAuth 2.0 + SAML 2.0 + MFA enforcement on all user-facing routes.
- **Authorization**: RBAC with fine-grained permissions; no role escalation without explicit policy.
- **Network**: All sandbox Docker containers must have strict egress network policies (no arbitrary outbound).
- **PII**: All outputs must pass PII masking before storage or display.
- **Prompt injection**: All user-supplied text must pass injection detection before being included in agent prompts.
- **Audit logs**: 7-year retention on all access and action logs.
- **Penetration testing**: Quarterly third-party assessments — do not merge changes that could introduce new attack surfaces without security review.
- **Compliance targets**: GDPR, CCPA, SOC 2 Type II, ISO 27001.

---

## AI Safety & Guardrails

- **Content moderation**: Filter all generated code and copy to prevent harmful or illegal outputs.
- **Bias mitigation**: Strategist Agent prompts must use diversified system prompts to avoid Western-centric market bias.
- **Human-in-the-loop (HITL)**: Required approval gates before:
  - Infrastructure spend (DevOps Agent)
  - Public posting (Marketer Agent — Launch Control Center)
  - Architecture decisions (Architect Agent — Founder approval gate)
- **LLM-as-judge**: Second LLM must score readability and maintainability before code is marked as final.
- **Hallucination check**: Marketing copy must be cross-referenced with generated feature list before approval.

---

## Performance Targets (Non-Negotiable)

| Metric | Target |
|---|---|
| UI response time | < 100ms |
| Sandbox spin-up | < 10 seconds |
| End-to-end MVP generation | < 15 minutes |
| End-to-end deploy | < 10 minutes |
| Validation cycle | < 30 minutes |
| Self-healing auto-fix rate | ≥ 90% |
| First-run deploy success rate | ≥ 85% |
| Concurrent builds (horizontal scale) | 500 |
| COGS per MVP | < ₹500 |

---

## Model Routing Policy

Use the cheapest capable model for each task:

| Task complexity | Model |
|---|---|
| Complex reasoning, architecture, self-healing | Claude Sonnet (latest) |
| Standard code gen, marketing copy | GPT-4o |
| Simple CRUD generation, formatting, classification | GPT-4o-mini |
| Image / visual asset generation | DALL-E 3 or Midjourney |

> Do not default everything to the most expensive model. The LLMOps Agent tracks per-task cost; regressions in COGS will be flagged.

---

## Development Conventions

### Git
- Branch naming: `feat/<pillar>/<short-description>`, e.g. `feat/coder-agent/stripe-integration`
- Every agent change requires a PR; no direct pushes to `main`.
- PRs must pass: lint, unit tests, security scan (Trivy + Semgrep), and LLM-as-judge eval.

### Code Quality
- TypeScript strict mode (`"strict": true`) everywhere in JS/TS code.
- Python: type hints required on all public functions; mypy must pass.
- All new API routes must have a corresponding OpenAPI spec entry.
- Generated code must include: Dockerfile, docker-compose.yml, GitHub Actions workflow, README.

### Testing
- Unit tests: Jest (TS), pytest (Python)
- Integration tests: Playwright (E2E), sandbox API endpoint tests
- AI evals: LLM-as-judge scoring via LangSmith on every agent output
- Load test baseline: simulate Product Hunt spike (sudden burst traffic) before any deploy SLA is marked as met.

### Environment Separation
- `sandbox` — ephemeral Docker, used during build/test phase, torn down after
- `staging` — persistent, mirrors production config, used for smoke tests
- `production` — AWS EKS, ArgoCD-managed, zero-downtime rolling deploys only

---

## Common Commands

```bash
# Install dependencies (monorepo)
pnpm install

# Run API Gateway locally
pnpm --filter api dev

# Run web frontend locally
pnpm --filter web dev

# Run AI services locally
cd apps/ai-services && uvicorn main:app --reload

# Run all unit tests
pnpm test

# Run linting
pnpm lint

# Run security scan (requires Docker)
trivy fs . && semgrep --config auto .

# Terraform plan (infra changes)
cd infra/terraform && terraform plan -var-file=env/staging.tfvars

# Run LangSmith eval suite
cd packages/agents && python evals/run_evals.py
```

---

## Key Integrations Reference

| Category | Service | Used By |
|---|---|---|
| Search / Research | Tavily, SerpAPI, Crunchbase, G2 | Strategist |
| Payments | Stripe | Coder, Pricing Agent |
| Auth | Auth0 | Coder, API Gateway |
| Email | Resend / SendGrid | Marketer, Coder |
| Social | X API, LinkedIn API, Reddit API | Marketer |
| Launch | ProductHunt API | Marketer |
| Image gen | DALL-E 3, Midjourney | Marketer |
| DNS / SSL | Route53, Let's Encrypt | DevOps |
| Secrets | AWS Secrets Manager | DevOps, all agents |
| Tracing | LangSmith | LLMOps |
| Metrics | Prometheus + Grafana | LLMOps, DevOps |
| Logs | CloudWatch + Fluent Bit | All |
| Error tracking | Sentry | All |

---

## Open Questions (Do Not Assume — Escalate)

These are unresolved at the time of this document. Do not implement solutions for these without explicit product decision:

1. How to automate "Transfer of Ownership" of AWS accounts when users eject from the SaaS?
2. Multi-cloud support (GCP / Azure) for AI Researchers testing multi-cloud agents?
3. Approach for preventing commoditization of differentiating features over time.
4. Mobile app generation (Pillar 8 — Phase 2 scope, not yet designed).

---

## Phases / What's In Scope Now

| Phase | Status | Scope |
|---|---|---|
| Phase 1 — Validation Engine | **Active** | Strategist Agent, competitor analysis, Lean Canvas |
| Phase 2 — MVP Builder | Upcoming | Coder + Reviewer Agent, sandbox, containerization |
| Phase 3 — Launch & GTM | Planned | Marketer Agent, social integrations |
| Phase 4 — Enterprise Scale | Planned | LLMOps, CT pipelines, full AWS deploy automation |
| Phase 5 — Global Expansion | Planned | Multi-region, localization, marketplace |

> **Out of scope for all current phases**: native mobile apps, high-frequency trading systems, regulated medical software.

---

## Pricing Tiers (for context in generated copy / billing logic)

| Tier | Price | Builds | Notes |
|---|---|---|---|
| AI Deep Researcher / Solopreneur | ₹10,000/mo | 1 active | Sandbox only |
| Startup Founder / Product Manager | ₹50,000/mo | 5/mo | 1-click AWS/Azure deploy |
| Enterprise / Agency | Custom | Unlimited | Dedicated VPC, on-prem LLM, white-labeling |

---

*Document prepared by the Euron Auto-Founder AI Product Team | May 2026*
*For questions: product@euron.one*
