# AutoFounder AI — Codebase Summary

> **Version**: 1.0 · **Date**: 2026-05-26  
> **Authoritative reference**: `CLAUDE.md` (full 10-layer architecture)  
> **Task tracker**: `.claude/TASKS.md` (AF-001 – AF-078)

---

## 1. What This Project Is

AutoFounder AI is a **multi-tenant, agentic AI SaaS platform** that converts a single text idea into a fully validated, designed, built, tested, deployed, marketed, and continuously-improved software business — autonomously, in approximately 7 days.

| Metric | Traditional | AutoFounder AI |
|--------|-------------|----------------|
| Idea → Validated | 3 weeks | 30 minutes |
| Validated → MVP | 3–6 months | 7 days |
| MVP → Deployed | 1 week | 10 minutes |
| Total Cost | $20K–$60K | < ₹500 COGS |

**7-pillar pipeline**: Strategy & Ideation → Architecture → Code Gen → Testing & Self-Healing → Deploy → Marketing & Launch → LLMOps  
**Org**: Euron AutoFounder AI · Bengaluru, Karnataka · `product@euron.one`

---

## 2. Build Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Monorepo & Boilerplate Setup (AF-001 – AF-011) | ✅ **Complete** |
| Phase 2 | Infrastructure & Cloud — AWS, Supabase, CI/CD (AF-012 – AF-024) | ❌ Pending |
| Phase 3 | Backend — FastAPI + LangGraph + Agents (AF-025 – AF-050) | ❌ Pending |
| Phase 4 | Frontend — Next.js 14 Founder Portal (AF-051 – AF-062) | ❌ Pending |
| Phase 5 | Mobile — Expo React Native (AF-063 – AF-071) | ❌ Pending |
| Phase 6 | VS Code Extension (AF-072 – AF-078) | ❌ Pending |

**What is actually running today**: the marketing `website/` (React + Vite) deployed to Vercel — all other components are scaffolds/placeholders.

---

## 3. Repository Root

```
AutoFounder-AI/CodeBase/
│
├── .claude/                   Claude Code config, memory, tasks, and specs
├── .github/                   GitHub Actions CI/CD workflows
├── backend/                   FastAPI service — Python 3.12 (placeholder)
├── frontend/                  Next.js 14 Founder Portal (placeholder)
├── mobile-app/                Expo React Native app (placeholder)
├── vscode-extension/          VS Code Extension (placeholder)
├── website/                   Marketing landing page — React + Vite (LIVE on Vercel)
├── docs/                      Architecture documentation
├── scripts/                   Cross-platform setup scripts
├── infra/                     (not yet created) — Terraform AWS modules planned
│
├── Makefile                   Canonical task runner
├── package.json               Root pnpm workspace + Turborepo config
├── pnpm-workspace.yaml        Declares: frontend, mobile-app, vscode-extension
├── turbo.json                 Turborepo task pipeline (dev, build, lint)
├── eslint.config.mjs          Shared ESLint v9 flat config for all JS/TS packages
├── docker-compose.yml         Redis 7 only (Supabase CLI handles DB/Auth/Storage/Realtime)
├── .env.example               Required env vars (Supabase + Gemini)
├── .gitignore
├── README.md                  Product Requirements Document (PRD)
└── projectstructure-steps.txt Setup steps log
```

> **Note**: `website/` is NOT a pnpm workspace package — it has its own `package-lock.yaml` and `node_modules/`, managed independently with `npm`. It is not listed in `pnpm-workspace.yaml`.

> **Note**: `infra/` does not exist yet. All Terraform work is Phase 2 (AF-012–AF-024).

---

## 4. Directory Detail

### 4.1 `.claude/` — AI Agent Config

All Claude Code context, conventions, and planning files.

```
.claude/
├── CLAUDE.md         Full 10-layer architecture reference — AUTHORITATIVE
├── MEMORY.md         Quick-reference: stack decisions, commands, key facts
├── TASKS.md          Phase-by-phase task tracker (AF-001 – AF-078)
├── SKILL.md          Dev skill: when to activate, conventions, checklists
├── SUMMARY.md        ← this file
├── PLAN.md           (empty)
├── PLAN_PHASE.md     (empty)
└── specs/
    ├── api-design.md     REST conventions, response envelope, error codes, pagination, WebSocket
    ├── database.md       PostgreSQL schema design, Redis key schema, Alembic rules
    ├── deployment.md     ⚠️ STALE — references GCP Cloud Run; authoritative target is AWS ECS Fargate
    ├── integrations.md   ⚠️ STALE — references Auth0 + OpenAI + Anthropic; resolved: Supabase Auth + Gemini
    ├── mobile.md         Expo conventions, EAS profiles, push notifications, navigation
    └── stack.md          ⚠️ STALE — lists GCP as cloud; resolved: AWS + Terraform per CLAUDE.md
```

**Stale specs warning**: `specs/deployment.md`, `specs/integrations.md`, and `specs/stack.md` were written before the tech-stack consolidation. `CLAUDE.md` overrides them on all conflicting points. Do not rely on these for infrastructure, auth, or LLM provider decisions.

---

### 4.2 `backend/` — FastAPI Service (Python 3.12)

**Status**: Scaffold/placeholder — no application logic yet. Phase 3 (AF-025+) will build this out.

```
backend/
├── src/
│   └── codepilot/          ⚠️ Package named 'codepilot' (placeholder name; will be renamed)
│       └── __init__.py     version = "0.0.0" + docstring
├── docker/
│   └── placeholder_http_server.py   Minimal HTTP health-check server (returns "ok\n")
├── pyproject.toml          Dependencies + Ruff + Hatch build config
├── Dockerfile              python:3.12-slim; runs placeholder HTTP server on PORT=8080
└── README.md
```

**`pyproject.toml` dependencies** (full production stack declared, not yet implemented):

| Package | Purpose |
|---------|---------|
| `fastapi>=0.115.0` | Async API framework |
| `uvicorn[standard]>=0.32.0` | ASGI server |
| `supabase>=2.9.0` | Supabase client (PostgreSQL + pgvector + Storage + Realtime) |
| `pgvector>=0.3.0` | pgvector Python types |
| `asyncpg>=0.29.0` | Async PostgreSQL driver |
| `sqlalchemy[asyncio]>=2.0.0` | ORM + async session |
| `google-generativeai>=0.8.0` | Gemini 3.5 Flash + gemini-embedding-2 |
| `langgraph>=0.2.0` | Stateful DAG orchestration |
| `prometheus-client>=0.21.0` | Metrics |
| `opentelemetry-sdk>=1.28.0` | Distributed tracing |
| `opentelemetry-exporter-otlp>=1.28.0` | OTel OTLP exporter |
| `confluent-kafka>=2.6.0` | Kafka producer/consumer |

**Dev deps**: `ruff>=0.8.0`  
**Python**: `>=3.12`  
**Package manager**: `uv` (`uv sync --all-groups`)

**Dockerfile note**: Currently runs a placeholder Python HTTP server. Dockerfile comment says role is determined via `AUTOFOUNDER-AI_ROLE` env var — api / orchestrator / worker will share the same image.

---

### 4.3 `frontend/` — Next.js 14 Founder Portal (Placeholder)

**pnpm package name**: `@autofounder-ai/frontend-web`  
**Status**: TypeScript placeholder only. Full Next.js 14 implementation is Phase 4 (AF-051+).

```
frontend/
├── src/
│   └── placeholder.ts    Empty placeholder
├── package.json          Scripts: dev (console.log placeholder), lint, format
└── tsconfig.json
```

**Planned surfaces** (per CLAUDE.md §14):
- Idea Intake (multi-modal: text, PDF, voice, URL)
- Validation Studio (Lean Canvas, viability gauge, pivot picker)
- Architecture Studio (ERD renderer, Swagger UI, cost forecast)
- Code Review Studio (Monaco diff viewer, Reviewer comments)
- Deploy Console (live log stream, rollback button)
- Launch Control Center (brand kit, social drafts, approve/edit gate)
- LLMOps Dashboard (cost by model/pillar, drift scores, eval history)

**Planned tech**: Next.js 14 App Router · React 18 · Tailwind CSS · shadcn/ui · Zustand · React Query · Supabase Realtime (live token/step stream) · Supabase Auth (`@supabase/supabase-js` + `@supabase/ssr`)

---

### 4.4 `mobile-app/` — Expo React Native (Placeholder)

**pnpm package name**: `@autofounder-ai/mobile-app`  
**Status**: TypeScript placeholder only. Phase 5 (AF-063+).

```
mobile-app/
├── src/
│   └── placeholder.ts
├── package.json          Scripts: dev (console.log placeholder), lint, format
└── tsconfig.json
```

**Planned features**: Idea intake (text, voice, file), run dashboard, live step log stream, HITL gate approvals (offline-queued), artifacts viewer, push notifications (FCM), LLMOps summary.

**Planned tech**: Expo SDK (managed workflow) · Expo Router (file-based navigation) · React Query · `expo-secure-store` (auth tokens) · EAS Build + Submit · iOS 16+ and Android 13+.

**Detailed spec**: `.claude/specs/mobile.md`

---

### 4.5 `vscode-extension/` — VS Code Extension (Placeholder)

**pnpm package name**: `@autofounder-ai/vscode-extension`  
**Status**: TypeScript placeholder only. Phase 6 (AF-072+).

```
vscode-extension/
├── src/
│   └── placeholder.ts
├── package.json    engines.vscode: "^1.85.0"; scripts: dev, lint, format
└── tsconfig.json
```

**Planned features**: Run list sidebar (status icons, cost badge), HITL gate notifications (inline approve/reject), code-gen commands (`AutoFounder: Generate Component`, `AutoFounder: Generate API Endpoint`), live token streaming panel (WebviewPanel), artifact quick-open (Lean Canvas, ERD, OpenAPI spec).

---

### 4.6 `website/` — Marketing Landing Page (LIVE)

**Status**: Fully built and deployed to Vercel via GitHub Actions.  
**Tech**: React 19 + TypeScript + Tailwind CSS v4 + Vite 8 · `lucide-react` for icons.

```
website/
├── src/
│   ├── App.tsx                    Root — composes all landing sections
│   ├── main.tsx                   React entry point
│   ├── index.css + App.css        Global styles
│   └── components/landing/
│       ├── Navbar.tsx
│       ├── Hero.tsx               Main headline + CTA
│       ├── VideoSection.tsx       Product demo video
│       ├── Problem.tsx            The 4 founder failures + ROI table
│       ├── Features.tsx           7-pillar feature highlights
│       ├── HowItWorks.tsx         Step-by-step flow
│       ├── Testimonials.tsx
│       ├── Pricing.tsx            3 tiers (₹10k/₹50k/Enterprise)
│       ├── Waitlist.tsx           Email capture
│       ├── FAQ.tsx
│       └── Footer.tsx
├── public/
│   ├── favicon.svg
│   └── icons.svg
├── dist/                          Production build output (committed)
├── vercel.json                    Vercel deploy config
├── vite.config.ts
├── index.html
└── package.json                   name: "autofounder-website" (uses npm, not pnpm)
```

**Deploy**: `.github/workflows/deploy-frontend.yml` — triggers on push to `main` when `website/**` changes → `pnpm build` → Vercel production deploy.

---

### 4.7 `docs/architecture/`

Full architecture documentation written and maintained.

```
docs/architecture/
├── HLD.md                         High-Level Design — 16 sections, ~850 lines
├── LLD.md                         Low-Level Design — module breakdown, schemas, sequences ~2,500 lines
├── architecture.md                Mermaid diagrams — system, workflow, data architecture
└── Agents-Architecture/
    ├── strategist-agent.md        Pillar 1 — Strategy & Ideation agent spec
    ├── architect-agent.md         Pillar 2 — Architect sub-agent spec
    ├── coder-agent.md             Pillar 3 — Coder sub-agent spec
    ├── reviewer-agent.md          Pillar 4 — Reviewer / Self-Healer spec
    ├── devops-agent.md            Pillar 5 — DevOps sub-agent spec
    ├── marketer-agent.md          Pillar 6 — Marketing agent spec
    └── llmops-agent.md            Pillar 7 — LLMOps agent spec
```

All three main docs (`HLD.md`, `LLD.md`, `architecture.md`) are up to date with the current tech stack (Gemini 3.5 Flash, Supabase pgvector, FastAPI, Supabase Realtime, Confluent Kafka).

---

### 4.8 `.github/workflows/`

```
.github/workflows/
└── deploy-frontend.yml    Vercel deploy for website/ on push to main
```

Full CI/CD pipeline (lint + typecheck + tests + security scans + ECR push + AWS CodeDeploy blue/green) is Phase 2, task AF-022.

---

### 4.9 `scripts/`

```
scripts/
├── dev-setup.sh     Bash — checks pnpm + uv, copies .env.example, pnpm install, uv sync, docker compose up
└── dev-setup.ps1    PowerShell equivalent for Windows
```

> **Note**: `dev-setup.sh` still mentions "PostgreSQL + Redis started (docker compose)" — stale. Docker Compose now runs Redis only; Supabase CLI (`supabase start`) handles the database stack.

---

## 5. Monorepo Tooling

### pnpm + Turborepo

| Tool | Role |
|------|------|
| `pnpm@9.15.9` | JS/TS package manager; hoisted `node_modules` |
| `Turborepo@2.4.2` | Task orchestration (caching, parallelism) |
| `typescript@5.7.3` | Shared TypeScript version across all JS packages |
| `eslint@9.19.0` | ESLint v9 flat config (`eslint.config.mjs` at root) |
| `prettier@3.4.2` | Code formatting across all JS/TS files |

**Turborepo pipelines** (`turbo.json`):

| Task | Behaviour |
|------|-----------|
| `dev` | Runs all workspaces in parallel; no caching (`persistent: true`) |
| `build` | Depends on upstream `^build`; caches `dist/**` |
| `lint` | Depends on upstream `^lint` |

**pnpm workspaces** (`pnpm-workspace.yaml`): `frontend`, `mobile-app`, `vscode-extension`.  
`backend/` and `website/` are **not** pnpm workspaces — backend uses `uv`, website uses npm.

### Makefile targets

| Target | Command |
|--------|---------|
| `make install` | `pnpm install` + `cd backend && uv sync --all-groups` |
| `make stack` | `docker compose up -d` (Redis only) |
| `make stack-down` | `docker compose down` |
| `make dev` | `pnpm dev` → `turbo dev` |
| `make backend-lint` | `ruff check src` + `ruff format --check src` |
| `make backend-format` | `ruff format src` + `ruff check --fix src` |
| `make js-lint` | `pnpm lint` → `turbo lint` |
| `make quality` | `backend-lint` + `js-lint` (must both pass before any PR) |

---

## 6. Environment Variables

**`.env.example`** — required vars:

```bash
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
DATABASE_URL=

# Gemini
GEMINI_API_KEY=
```

All other secrets (Stripe, Resend, GitHub App, LangSmith, Sentry) go into AWS Secrets Manager — never `.env` files in the repo.

---

## 7. Tech Stack (Authoritative)

### Backend
| Concern | Choice |
|---------|--------|
| Language | Python 3.12 |
| Framework | FastAPI (async, OpenAPI 3.1 auto-gen) |
| Package manager | `uv` (lockfile: `uv.lock`) |
| Linting / format | Ruff (`line-length=100`, `select=E,F,I,UP,B`) |
| Orchestration | LangGraph (stateful DAGs, HITL gates, Postgres+Redis checkpoints) |
| LLM | Gemini 3.5 Flash (all task classes via LiteLLM router) |
| Embeddings | gemini-embedding-2 — 768 dimensions |
| Message bus | Confluent Kafka (primary) + EventBridge + SQS/SNS |

### Frontend / Clients
| Concern | Choice |
|---------|--------|
| Founder Portal | Next.js 14 App Router + React 18 + Tailwind CSS + shadcn/ui |
| State | Zustand (UI) + React Query (server) + Supabase Realtime (live stream) |
| Auth | Supabase Auth (`@supabase/supabase-js` + `@supabase/ssr`) |
| Mobile | Expo (React Native) — iOS 16+ / Android 13+ |
| VS Code | TypeScript + VS Code API |
| Monorepo | pnpm + Turborepo |

### Data
| Concern | Choice |
|---------|--------|
| Relational + Vector | Supabase (PostgreSQL + pgvector `vector(768)` HNSW + Storage + Realtime + Auth) |
| Isolation | Schema-per-tenant + RLS |
| Cache | Redis 7 — ElastiCache (prod) / Docker Compose (local) |
| Graph | Neo4j / Amazon Neptune (competitor ↔ market ↔ persona) |
| Object storage | Supabase Storage (app artifacts) + S3 (RLHF data lake, 7-yr audit) |
| Data access | UDAL (`packages/db`) — agents must never touch DB drivers directly |

### Infrastructure
| Concern | Choice |
|---------|--------|
| Cloud | AWS (ECS Fargate, multi-AZ VPC) |
| IaC | Terraform (planned, `infra/` not yet created) |
| Deploy strategy | GitHub Actions → AWS CodeDeploy (ECS blue/green) |
| Local dev DB | Supabase CLI (`supabase start`) |
| Container registry | Amazon ECR |
| Secrets | AWS Secrets Manager + SSM Parameter Store |
| Observability | Prometheus + Grafana + OpenTelemetry + LangSmith |

---

## 8. Local Development Quickstart

```bash
# 1. Install all dependencies
make install          # pnpm install + uv sync --all-groups

# 2. Copy env
cp .env.example .env  # fill in Supabase + Gemini keys

# 3. Start Supabase (PostgreSQL + pgvector + Auth + Storage + Realtime)
supabase start

# 4. Start Redis
make stack            # docker compose up -d

# 5. Run all frontend workspaces (dev mode)
make dev              # turbo dev

# 6. Run backend (once FastAPI is scaffolded in Phase 3)
cd backend && uv run uvicorn autofounder_ai.main:app --reload --port 8000

# 7. Quality gate before any PR
make quality          # backend ruff + js eslint — must pass
```

---

## 9. Branch Strategy

```
main            → production-ready; protected; no direct push
  └── testing   → integration + QA; merges to main via PR
        └── dev → active development; feature branches merge here
```

Feature branches: `feature/AF-NNN-kebab-description` (e.g. `feature/AF-037-strategy-agent`)  
Hotfixes: `hotfix/kebab-description` → PR to `main` + back-merge  
All merges via PR; `make quality` + tests + security scan must pass.

---

## 10. Key Known Issues / Stale References

| Location | Issue | Authoritative source |
|----------|-------|---------------------|
| `scripts/dev-setup.sh` | Says "PostgreSQL + Redis" for docker compose — now Redis only | `docker-compose.yml` |
| `Makefile` | `make stack` comment says "Start local databases (PostgreSQL + Redis)" — now Redis only | `docker-compose.yml` |
| `.claude/specs/deployment.md` | Entire spec references GCP Cloud Run, not AWS ECS Fargate | `CLAUDE.md §17` |
| `.claude/specs/integrations.md` | References Auth0 + OpenAI + Anthropic as primary | `CLAUDE.md §31` (Supabase Auth + Gemini) |
| `.claude/specs/stack.md` | Lists GCP as cloud choice; primary LLM marked "pending" | `CLAUDE.md §48` |
| `.claude/specs/mobile.md` | References Auth0 and `ws-client.ts` | `CLAUDE.md §14` (Supabase Auth + Realtime) |
| `PLAN.md` / `PLAN_PHASE.md` | Both empty | — |
| `test.txt` | Stray file at repo root | Can be deleted |

---

## 11. Documentation Quick-Nav

| Need | File |
|------|------|
| Full system architecture (10 layers, agents, memory, guardrails) | `CLAUDE.md` |
| High-level diagrams and flow | `docs/architecture/HLD.md` |
| Module breakdown, DB schemas, API sequences | `docs/architecture/LLD.md` |
| Mermaid system / data / workflow diagrams | `docs/architecture/architecture.md` |
| Individual agent specs | `docs/architecture/Agents-Architecture/*.md` |
| REST API conventions and error codes | `.claude/specs/api-design.md` |
| PostgreSQL schema + Redis key design | `.claude/specs/database.md` |
| Mobile (Expo) conventions | `.claude/specs/mobile.md` |
| Task list and build progress | `.claude/TASKS.md` |
| Stack decisions and rationale | `.claude/MEMORY.md` |
| Dev conventions and checklists | `.claude/SKILL.md` |