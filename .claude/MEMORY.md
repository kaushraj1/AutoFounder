# AutoFounder AI — Claude Memory

> **AutoFounder AI** is a multi-tenant agentic AI SaaS that converts a single text idea into a
> fully validated, built, deployed, and marketed software business autonomously — cutting the
> traditional 4–7 month, $20–60K founder journey down to ~7 days at < ₹500 COGS per MVP.

---

## Product Identity

| Field | Value |
|-------|-------|
| **Name** | AutoFounder AI |
| **Type** | Multi-tenant agentic AI SaaS |
| **Target users** | Solo founders, product managers, startup teams |
| **Core promise** | Idea → live MVP in ~7 days without a dev team |
| **Tiers** | Solopreneur (₹10k/mo · 1 build), Startup (₹50k/mo · 5 builds), Enterprise (custom) |
| **MVP scope** | Phase 1–3: Strategy agent + Architect agent + Coder agent → deployed MVP |
| **Out of scope (v1)** | Mobile app generation, HFT, regulated medical software |

**7-pillar pipeline**: Strategy & Ideation → Architecture → Code Gen → Testing & Self-Healing → Deploy → Marketing & Launch → LLMOps

HITL gates required at: Pillar 1 (validation), Pillar 2 (architecture), Pillar 5 (infra spend), Pillar 6 (launch).

---

## Tech Stack Decisions

### Backend
| Concern | Choice | Why |
|---------|--------|-----|
| Language | Python 3.12 | Agent/ML ecosystem, type hints enforced |
| Framework | FastAPI | Async-native, OpenAPI 3.1 auto-gen, fast iteration |
| Package manager | `uv` | Deterministic, fast, replaces pip + venv |
| Linting/format | Ruff + `ruff format` | Single tool replacing Flake8 + isort + Black |
| Orchestration | LangGraph | Stateful DAGs, native HITL gates, deterministic checkpoints |

### Frontend / Clients
| Concern | Choice | Why |
|---------|--------|-----|
| Web portal | React + TypeScript (Next.js 14 App Router) | SSR + RSC, Tailwind + shadcn/ui |
| Mobile | Expo (React Native) | Cross-platform iOS/Android, EAS Build pipeline |
| VS Code extension | TypeScript + VS Code API | In-editor HITL approvals + code gen commands |
| Monorepo | pnpm + Turborepo | Workspace caching, parallel task execution |

### Infrastructure
| Concern | Choice |
|---------|--------|
| Cloud | AWS + Terraform (ECS Fargate, multi-AZ VPC) |
| Relational + Vector DB | Supabase (PostgreSQL + pgvector + Storage + Auth + Realtime) — hosted, schema-per-tenant |
| Cache | Redis 7 — ElastiCache (production) / Docker Compose (local) |
| Message bus | Confluent Kafka (primary inter-agent events + LLMOps telemetry) + EventBridge + SQS/SNS |
| Object storage | Supabase Storage (app artifacts) + Amazon S3 (RLHF data lake, audit archive 7-yr) |
| Local dev | Supabase CLI (`supabase start`) for DB/Auth/Storage/Realtime + Docker Compose for Redis |
| Auth | Supabase Auth — OAuth 2.0, JWT (SUPABASE_JWT_SECRET), MFA enforced |
| CI/CD | GitHub Actions → AWS CodeDeploy (ECS blue/green) |

### LLMs & Embeddings
| Concern | Choice |
|---------|--------|
| Primary LLM | Gemini 3.5 Flash (all task classes — reasoning, code gen, marketing, classification) |
| Embeddings | gemini-embedding-2 — 768 dimensions — all 7 vector collections |
| Image generation | DALL-E 3, Midjourney, Stable Diffusion |
| Speech | Whisper |
| Safety classifier | Llama Guard 3 |
| Router | LiteLLM (cheapest-capable routing) |

---

## Directory Layout

```
<<<<<<< HEAD
autofounder-ai/
├── backend/               FastAPI service (Python 3.12, uv)
│   ├── src/autofounder-ai/   application source
│   ├── pyproject.toml        uv + Ruff config
│   └── Dockerfile
├── frontend-web/          Next.js 14 Founder Portal (pnpm workspace)
│   └── src/
├── mobile-app/            Expo React Native (pnpm workspace)
│   └── src/
├── vscode-extension/      VS Code Extension (pnpm workspace)
│   └── src/
├── infra/                 Terraform modules (AWS) — not yet created
├── docs/
│   └── architecture/      HLD.md · LLD.md · architecture.md
=======
autofounder-ai/                        (per CLAUDE.md §40 — authoritative)
├── apps/
│   ├── api/               FastAPI API Gateway (Python 3.12, uv)
│   │   ├── src/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   ├── orchestrator/      LangGraph engine (Python 3.12)
│   ├── ai-services/       FastAPI agent workers (Python 3.12)
│   ├── web/               Next.js 14 Founder Portal (pnpm workspace)
│   └── admin/             Next.js super-admin dashboard (pnpm workspace)
│   # Realtime: Supabase Realtime (managed — no separate service)
├── packages/
│   ├── agents/            Agent implementations (Python)
│   │   ├── strategy/
│   │   ├── product_planner/
│   │   ├── research/
│   │   ├── engineering/   architect/ · coder/ · reviewer/ · devops/
│   │   ├── marketing/
│   │   ├── finance/
│   │   ├── ops_risk/
│   │   └── llmops/
│   ├── guardrails/        6-stage guardrails pipeline (Python)
│   ├── prompts/           Versioned Jinja2 prompt templates
│   ├── tools/             MCP-style tool definitions
│   ├── db/                UDAL + SQLAlchemy + Supabase migrations
│   ├── shared/            Shared types, utils, constants
│   └── eval/              Promptfoo + LangSmith golden sets
├── infra/
│   ├── terraform/         IaC for AWS (ECS, ElastiCache, S3, messaging, IAM…)
│   └── codedeploy/        Blue/green deploy specs
├── docs/
│   └── architecture/      HLD.md · LLD.md · architecture.md · Agents-Architecture/
>>>>>>> dev
├── scripts/
│   ├── dev-setup.sh
│   └── dev-setup.ps1
├── .claude/
│   ├── MEMORY.md          ← this file
│   ├── TASKS.md
│   └── settings.local.json
├── docker-compose.yml     Redis 7 only (Supabase CLI handles DB/Auth/Storage/Realtime locally)
├── Makefile               canonical task runner
├── turbo.json             Turborepo pipeline config
├── pnpm-workspace.yaml
<<<<<<< HEAD
├── CLAUDE.md              full architecture reference
└── TASKS.md               phase-by-phase task tracker (AF-001 … AF-078)
=======
└── CLAUDE.md              full architecture reference
>>>>>>> dev
```

---

## Key Commands

```bash
# One-time setup
make install          # pnpm install + uv sync --all-groups

# Local Supabase (PostgreSQL + pgvector + Auth + Storage + Realtime)
supabase start        # start all Supabase services locally
supabase stop         # stop Supabase services

# Local Redis
make stack            # docker compose up -d  (Redis only)
make stack-down       # docker compose down

# Run everything (Turborepo parallel)
make dev              # pnpm dev  →  turbo dev

# Quality gates (run before every PR)
make quality          # backend-lint + js-lint (must both pass)
make backend-lint     # uv run ruff check src + ruff format --check src
make backend-format   # uv run ruff format src + ruff check --fix src
make js-lint          # pnpm lint  →  turbo lint
make js-format        # pnpm format  →  prettier --write .

# Run backend tests (once test suite exists)
cd backend && uv run pytest

# Turbo tasks directly
pnpm dev              # all workspaces in parallel
pnpm lint             # all JS/TS workspaces
pnpm build            # production builds
```

---

## Branch Strategy

```
main          production-ready, protected — no direct push
  └── testing     integration + QA — merges to main via PR
        └── development   active development — feature branches merge here
```

- Feature branches: `feature/<task-id>-<kebab-description>` (e.g. `feature/AF-037-strategy-agent`)
- Hotfixes: `hotfix/<kebab-description>` → PR directly to `main` + back-merge to `development`
- All merges via PR; CI must pass (`make quality` + tests + security scan)

---

## Coding Conventions

> **To be filled by the team.** Placeholder entries below.

- [ ] API response envelope format (e.g. `{data, error, requestId}`)
- [ ] Error code naming scheme (`AF_ERR_*` vs HTTP status only)
- [ ] Async vs sync FastAPI route conventions
- [ ] Python type hint strictness level (`strict` mypy or `basic`)
- [ ] Component naming in React (PascalCase files, named exports)
- [ ] State management split: what lives in Zustand vs React Query vs local state
- [ ] Commit message format (Conventional Commits enforced by hook?)
- [ ] Test file colocation vs `tests/` directory

---

## Things Not Yet Decided

- [x] ~~GCP services mapping~~ **RESOLVED**: AWS (ECS Fargate, multi-AZ VPC, ElastiCache, S3, ECR, Secrets Manager)
- [x] ~~Vector store~~ **RESOLVED**: Supabase pgvector — `vector(768)` HNSW index, schema-per-tenant; eliminates separate vector DB
- [x] ~~Primary LLM for agents~~ **RESOLVED**: Gemini 3.5 Flash (all task classes) + gemini-embedding-2 (768-dim embeddings)
- [x] ~~Tenant DB isolation strategy~~ **RESOLVED**: schema-per-tenant + RLS as defense-in-depth
- [ ] Graph DB — Neo4j vs Amazon Neptune — pending benchmark on competitor ↔ market ↔ persona queries
- [ ] Feature flag service — LaunchDarkly vs GrowthBook vs Statsig
- [ ] Multi-region strategy — single AWS region (ap-south-1, Mumbai) for v1 or multi-region from day one
- [ ] Mobile platforms for v1 — iOS + Android simultaneously or iOS-first

---

## Changelog

| Date | Version | Description |
|------|---------|-------------|
| 2026-05-20 | 1.0.0 | Initial MEMORY.md created — product identity, stack decisions, directory layout, commands, branch strategy |
| 2026-05-26 | 1.1.0 | Tech stack alignment: AWS replaces GCP; Supabase (PostgreSQL + pgvector + Storage + Auth + Realtime) replaces RDS + MongoDB Atlas + Auth0; Gemini 3.5 Flash + gemini-embedding-2 replaces Claude/GPT-4o; Confluent Kafka added; COGS updated to < ₹500; resolved decisions moved out of open questions |
