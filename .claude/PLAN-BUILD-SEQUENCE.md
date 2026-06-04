# AutoFounder AI — Master Build Plan

> **Status**: Active · **Phase**: 1 — Validation Engine  
> **Date**: 2026-05-30 · **Target**: 10 pilot clients  
> **Canonical authority**: `.claude/CLAUDE.md` overrides everything else (stack.md has stale GCP refs — ignore those)
>
> ⚠️ **PATHS IN THIS DOC ARE ILLUSTRATIVE/HISTORICAL.** This is the granular S0–S4 build-sequence companion to `.claude/PLAN.md` (master). The **authoritative** structure (see `.claude/CLAUDE.md` §40) is **one consolidated backend `backend/app/`** (api · orchestrator · agents · workers · db · guardrails · models · prompts · tools · core) + `frontend/` + `admin/` + `mobile-app/` + `infra/` + `packages/{shared,api-client}` (TypeScript-only). Read every `backend/src/autofounder_ai/` below as **`backend/app/`**, `frontend/` as **`frontend/`**, and `infra/` as **`infra/`**. The earlier 3-service split (api + orchestrator + ai-services) is now a single modular-monolith backend (split in Phase 4 if scale needs it). Canonical tenant key **`organization_id`**; auth **Supabase Auth**. Current plan: **`.claude/PLAN.md`** (master), **`.claude/PLAN_PHASE.md`** (active phase), **`.claude/TASKS.md`** (tasks).

---

## Current State Snapshot

| Area | State |
|---|---|
| Supabase | Connected (`hphyfoylvkkwhepaayoz.supabase.co`) — keys blank in .env |
| Kafka | Confluent Cloud provisioned (`pkc-l7pr2.ap-south-1`) — creds in .env.example |
| Redis | docker-compose ready, not started |
| Backend | Python/uv scaffolded in `backend/`; only a placeholder HTTP server, no FastAPI routes |
| Frontend | TS placeholder in `frontend/`; package name `@autofounder-ai/frontend` |
| Website | Vite/React landing page in `website/` — has actual code, keep as-is |
| Mobile | Expo placeholder in `mobile-app/` |
| VSCode Extension | TS placeholder in `vscode-extension/` |
| pnpm workspace | `pnpm-workspace.yaml` lists wrong path `frontend` (folder is `frontend/`) — broken |
| DB schemas | Fully designed in `.claude/specs/database.md` — not yet applied to Supabase |
| Docs | HLD, LLD, architecture.md, per-agent docs written |
| CI/CD | `deploy-frontend.yml` exists; no backend CI yet |

---

## Directory Layout (Locked — No Reorganization)

> ⚠️ **HISTORICAL TREE.** The authoritative tree is in `.claude/CLAUDE.md` §40 and `.claude/SUMMARY.md` §3: one consolidated **`backend/app/`** + `frontend/` (with super-admin `/admin` route group) + `mobile-app/` + `infra/` + `packages/{shared,api-client}`. The `backend/`-rooted tree below is retained for historical context only.

```
autofounder-ai/
├── backend/                      # FastAPI monolith — API gateway + Orchestrator + Agents
│   ├── src/
│   │   └── autofounder_ai/       # Python package (underscore — valid import)
│   │       ├── api/              # FastAPI app, middleware, routers
│   │       ├── orchestrator/     # LangGraph StateGraph, task router, HITL
│   │       ├── agents/           # Agent implementations
│   │       │   ├── base.py       # Agent ABC (understand/plan/execute/verify/learn)
│   │       │   ├── research/
│   │       │   ├── strategy/
│   │       │   └── product_planner/
│   │       ├── guardrails/       # 6-stage pipeline (input/instruction/exec/output/monitor)
│   │       ├── models/           # LLM clients — Gemini, LiteLLM router, embeddings
│   │       ├── prompts/          # Jinja2 templates + registry loader
│   │       ├── tools/            # MCP-style tool wrappers (Tavily, SerpAPI, etc.)
│   │       └── core/             # UDAL, config, Redis client, Kafka client, telemetry
│   ├── alembic/                  # DB migrations (env.py + versions/)
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                     # Next.js 14 Founder Portal (@autofounder-ai/frontend)
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   ├── components/
│   │   ├── hooks/
│   │   └── lib/
│   └── package.json
├── packages/                     # Shared JS-only packages (new)
│   └── shared-types/             # OpenAPI-generated TypeScript types (optional, Phase 2+)
├── website/                      # Marketing landing page (Vite/React) — keep as-is
├── mobile-app/                   # Phase 8 placeholder
├── vscode-extension/             # Placeholder
├── docs/                         # Architecture docs
├── infra/
│   └── terraform/                # AWS ECS Fargate IaC
├── .github/workflows/
├── turbo.json
├── pnpm-workspace.yaml
└── docker-compose.yml
```

**Key consequence**: all Python imports are `from autofounder_ai.core.udal import UDAL`, `from autofounder_ai.agents.strategy.agent import StrategyAgent` etc. One `uv` environment, one Dockerfile for backend.

---

## Guiding Principles

1. **Bottom-up**: infra/data → core platform → agents → frontend. Never build UI for an agent that doesn't exist.
2. **Phase 1 only**: Strategy Agent + Research Agent + Product Planner Agent. Nothing from Phase 2+.
3. **UDAL mandatory**: agents never touch DB directly — always through `autofounder_ai.core.udal`.
4. **Every layer has a guardrail wrapper** before shipping (even minimal version).
5. **Tenant isolation from day 0**: schema-per-org + RLS before first row written.
6. **Working software over docs**: each sprint ends with something runnable.

---

## 10-Layer Build Sequence

The 10 architecture layers must be built in dependency order, not presentation order.

```
Layer 5  (Data & Knowledge)          ← first: nothing works without persistent state
Layer 10 (Observability skeleton)    ← second: can't debug what you can't see
Layer 2  (Orchestration skeleton)    ← third: LangGraph + Kafka wiring
Layer 8  (Guardrails — minimal)      ← fourth: input/output filters before any LLM call
Layer 3  (Agents — Phase 1 trio)     ← fifth: Strategy + Research + Product Planner
Layer 4  (Model & Capability)        ← alongside Layer 3: Gemini client, RAG pipeline
Layer 1  (Input Layer — API GW)      ← sixth: FastAPI receives ideas, routes to orchestrator
Layer 6  (Output & Experience)       ← seventh: Founder Portal (Next.js)
Layer 7  (Service & Integration)     ← eighth: 3rd-party tools (Tavily, Resend, etc.)
Layer 9  (Compliance — minimal)      ← ninth: audit log, GDPR stubs
```

---

## Sprint Plan

### Sprint 0 — Foundation (Weeks 0–1)
**Goal**: Dev environment works end-to-end; data layer live; first API health-check returns 200.

#### S0.1 — Fix Workspace Config (immediate)
- [x] Fix `pnpm-workspace.yaml`: change `frontend` → `frontend` (folder name mismatch)
- [x] Fix `backend/pyproject.toml`: `packages = ["src/autofounder_ai"]` (hyphen → underscore)
- [ ] Create `backend/src/autofounder_ai/__init__.py` (empty — marks Python package)
- [ ] Create `packages/` dir with `packages/shared-types/` placeholder

#### S0.2 — Data Layer (Layer 5)
- [ ] Install Alembic: `uv add alembic psycopg2-binary` in `backend/`
- [ ] `backend/alembic/env.py` — async Alembic config pointing at `DATABASE_URL`
- [ ] Migration files:
  - `001_platform_schema.py` — `platform.organizations`, `platform.organization_keys`, `platform.model_registry`, `platform.prompt_registry`, `platform.tool_registry`, `platform.audit_log`
  - `002_org_schema_template.py` — `workspaces`, `runs`, `artifacts`, `gates`, `step_events`, `memory_episodes`, `cost_ledger` (PL/pgSQL function creates schema per org)
  - `003_pgvector.py` — enable extension, create `vector_collections` + `vector_entries` tables
  - `004_rls_policies.py` — RLS on every tenant table
- [ ] Apply migrations to Supabase (local `supabase start` + remote)
- [ ] `backend/src/autofounder_ai/core/udal.py` — `UDALClient` with `relational()`, `vector()`, `object()`, enforces `organization_id`, emits to `audit_log`
- [ ] `backend/src/autofounder_ai/core/redis_keys.py` — Redis key constants (org-prefixed)
- [ ] `backend/src/autofounder_ai/core/models.py` — SQLAlchemy ORM models
- [ ] Verify: `psql $DATABASE_URL -c "\dn"` shows `platform` schema; pgvector enabled

#### S0.3 — Observability Skeleton (Layer 10)
- [ ] `backend/src/autofounder_ai/core/telemetry.py`:
  - OTel SDK init (traces + metrics)
  - Structured logger factory (mandatory fields: `organization_id`, `pillar`, `agent_id`, `model`, `run_id`, `env`)
  - Prometheus counters: `agent_invocations_total`, `llm_latency_seconds`, `run_duration_seconds`
- [ ] LangSmith client init (reads `LANGSMITH_API_KEY`)
- [ ] Sentry init stub
- [ ] Verify: test script sends a span; shows in console exporter

#### S0.4 — FastAPI App skeleton (backend)
- [ ] `backend/src/autofounder_ai/api/main.py` — FastAPI app, startup/shutdown, CORS
- [ ] `backend/src/autofounder_ai/api/middleware/auth.py` — JWT validation, extracts `organization_id`, `role`, `scopes`
- [ ] `backend/src/autofounder_ai/api/middleware/rate_limit.py` — Redis-backed per-org limiter
- [ ] `backend/src/autofounder_ai/api/routers/health.py` — `GET /health`, `GET /ready`
- [ ] OTel middleware attached (every request traced)
- [ ] `backend/docker/placeholder_http_server.py` → delete; entrypoint becomes `uvicorn autofounder_ai.api.main:app`
- [ ] Update `backend/Dockerfile` entrypoint
- [ ] Verify: `cd backend && uv run uvicorn autofounder_ai.api.main:app --reload` → 200 on `/health`

#### S0.5 — Kafka Connectivity
- [ ] `backend/src/autofounder_ai/core/kafka.py` — typed producer/consumer wrappers
- [ ] Topic constants: `run.started`, `run.completed`, `pillar.completed`, `gate.required`, `human.approved`, `agent.failed`
- [ ] Create topics in Confluent Cloud (via admin client or Terraform)
- [ ] Verify: producer → consumer round-trip test passes

#### S0.6 — Environment & CI skeleton
- [ ] Populate `.env` with all keys (Supabase service role, Gemini, Kafka, LangSmith, Redis)
- [ ] `.env.example` sanitized — no real secrets (Kafka creds currently exposed — rotate if repo is public)
- [ ] `.github/workflows/ci.yml` — `ruff` + `mypy` + `pytest` (backend) + `tsc` + `eslint` (frontend)
- [ ] `Makefile` targets: `make dev`, `make lint`, `make test`, `make migrate`

---

### Sprint 1 — LangGraph Orchestrator + Guardrails (Weeks 1–2)
**Goal**: Orchestrator accepts a run, creates DB records, and routes through a minimal guardrail pipeline.

#### S1.1 — Orchestrator (Layer 2)
- [ ] `backend/src/autofounder_ai/orchestrator/graph.py` — LangGraph `StateGraph`
  - Nodes: `ingest → guardrail_input → route_to_agent → guardrail_output → checkpoint → emit_event`
  - State: `RunState(run_id, organization_id, pillar, step, artifacts, messages, error)`
- [ ] Checkpoint persistence: Postgres `platform.checkpoints` + Redis hot cache
- [ ] `backend/src/autofounder_ai/orchestrator/task_router.py` — Kafka consumer → dispatch
- [ ] `backend/src/autofounder_ai/orchestrator/hitl.py` — gate pause/resume logic
- [ ] Verify: `POST /v1/ideas` → DB row created → orchestrator picks up → transitions logged

#### S1.2 — Minimal Guardrails (Layer 8)
- [ ] `backend/src/autofounder_ai/guardrails/input.py` — PII regex + injection pattern + length check (5000 chars)
- [ ] `backend/src/autofounder_ai/guardrails/execution.py` — tool allow-list + per-org cost cap
- [ ] `backend/src/autofounder_ai/guardrails/output.py` — length check + toxicity stub
- [ ] All stages log to `platform.audit_log` via UDAL
- [ ] Verify: flagged input rejected with 422; audit entry written

#### S1.3 — Core API Routes
- [ ] `POST /v1/ideas` — validate, create run, enqueue to Kafka, return `run_id`
- [ ] `GET /v1/runs/{id}` — run state + gates
- [ ] `POST /v1/runs/{id}/gates/{gate_id}` — approve / reject
- [ ] `GET /v1/runs/{id}/artifacts` — list artifacts
- [ ] `GET /v1/runs/{id}/stream` — WebSocket via Supabase Realtime proxy
- [ ] OpenAPI 3.1 auto-generated at `/openapi.json`
- [ ] Verify: Postman/httpie hits all routes

---

### Sprint 2 — Phase 1 Agents (Weeks 2–4)
**Goal**: Submit idea → Lean Canvas + Viability Score + ICP personas in < 30 min.

#### S2.1 — Gemini Client + LiteLLM Router (Layer 4)
- [ ] `backend/src/autofounder_ai/models/llm.py` — LiteLLM wrapper (Gemini 3.5 Flash default, retry, streaming, cost tracking)
- [ ] `backend/src/autofounder_ai/models/embeddings.py` — `gemini-embedding-2` client, Redis cache (24h)
- [ ] Verify: test call → trace visible in LangSmith

#### S2.2 — Prompt Registry
- [ ] `backend/src/autofounder_ai/prompts/` — Jinja2 templates:
  - `strategy/market_sizing.j2`, `strategy/competitor_discovery.j2`, `strategy/persona_generation.j2`
  - `strategy/lean_canvas.j2`, `strategy/viability_scoring.j2`, `strategy/bias_audit.j2`
  - `research/market_research.j2`, `product_planner/prd_generation.j2`
- [ ] `backend/src/autofounder_ai/prompts/loader.py` — load by name+version, validate vars
- [ ] Seed `platform.prompt_registry` with v1.0.0 of each

#### S2.3 — Research Agent
- [ ] `backend/src/autofounder_ai/agents/base.py` — Agent ABC (`understand/plan/execute/verify/learn`)
- [ ] `backend/src/autofounder_ai/agents/research/agent.py`
- [ ] `backend/src/autofounder_ai/tools/tavily.py`, `tools/serpapi.py` — typed wrappers
- [ ] Tools registered in `platform.tool_registry`
- [ ] Output: `{market_signals, competitor_list, trends, sources[]}`
- [ ] Verify: "fitness app for remote workers" → competitor list returned

#### S2.4 — Strategy & Ideation Agent
- [ ] `backend/src/autofounder_ai/agents/strategy/agent.py`
- [ ] Sub-workflows as LangGraph nodes:
  1. `market_sizing` (TAM/SAM/SOM)
  2. `competitor_discovery`
  3. `persona_generation` (3–5 ICPs)
  4. `lean_canvas` (9-block Ash Maurya)
  5. `viability_scoring` (0–100)
  6. `bias_audit`
  7. `pivot_suggestions` (if score < 60)
- [ ] Reads `market_intelligence` pgvector namespace via UDAL (RAG)
- [ ] Writes to `artifacts` table; emits HITL gate `validation_approve`
- [ ] SLA: < 30 min; metric `pillar1_duration_seconds`
- [ ] Verify: full run → 7 artifacts + gate `pending`

#### S2.5 — Product Planner Agent
- [ ] `backend/src/autofounder_ai/agents/product_planner/agent.py`
- [ ] Inputs: approved Lean Canvas + personas
- [ ] Outputs: PRD (Markdown), feature list (MoSCoW), 3-sprint roadmap, user story map
- [ ] Artifacts written; triggered after Strategy gate approved
- [ ] Verify: PRD readable via `GET /v1/runs/{id}/artifacts`

#### S2.6 — Semantic Memory (pgvector)
- [ ] `backend/src/autofounder_ai/core/vector.py` — `upsert_embedding()`, `search_similar()` (HNSW, cosine)
- [ ] Collections: `market_intelligence`, `competitor_features`, `user_preferences`
- [ ] Embed key artifacts after each run
- [ ] Verify: second similar idea retrieves prior context

---

### Sprint 3 — Frontend Founder Portal v1 (Weeks 4–5)
**Goal**: Founder submits idea, watches live progress, approves gates from UI.

#### S3.1 — Next.js App Setup (frontend/)
- [ ] Install Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Zustand, React Query into `frontend/`
- [ ] Supabase Auth: magic link + Google OAuth
- [ ] Layout: sidebar nav, header with org switcher
- [ ] Protected routes (redirect unauthenticated to login)

#### S3.2 — Idea Intake Screen
- [ ] `frontend/src/app/(app)/ideas/new/page.tsx` — textarea (5000 char limit), file upload placeholder
- [ ] `POST /v1/ideas` on submit → redirect to run detail with `run_id`

#### S3.3 — Run Detail + Live Stream
- [ ] `frontend/src/app/(app)/runs/[id]/page.tsx`
- [ ] WebSocket hook → Supabase Realtime channel `run:{run_id}`
- [ ] Live step log, pillar progress bar (1 of 7)

#### S3.4 — Validation Studio (Pillar 1 HITL)
- [ ] `frontend/src/app/(app)/runs/[id]/validation/page.tsx`
- [ ] Lean Canvas grid, Viability gauge, ICP persona cards, competitor table, bias audit panel, pivot accordion
- [ ] Approve / Pivot → `POST /v1/runs/{id}/gates/{gate_id}`

#### S3.5 — PRD Viewer
- [ ] `frontend/src/app/(app)/runs/[id]/prd/page.tsx`
- [ ] Monaco editor (read-only), feature list, roadmap, user stories

---

### Sprint 4 — Hardening, Observability & Pilot Prep (Weeks 5–6)
**Goal**: Production-ready Phase 1 — 10 pilot clients can run end-to-end.

#### S4.1 — Full Guardrails (Layers 8 + 9)
- [ ] Stage 2: Presidio PII redaction (real, not regex stubs)
- [ ] Stage 5: TruLens hallucination check
- [ ] `platform.audit_log` → S3 daily export job (Object Lock)
- [ ] GDPR: `DELETE /v1/tenants/{id}` wipes all org data
- [ ] OPA policy file: `owner`, `member`, `viewer` RBAC

#### S4.2 — Full Observability (Layer 10)
- [ ] Prometheus `/metrics` on backend
- [ ] Grafana dashboard: pillar duration, LLM latency, cost, gate queue depth
- [ ] LangSmith project per run
- [ ] Sentry: frontend + backend errors
- [ ] Slack alert on `agent.failed` Kafka event

#### S4.3 — Multi-Tenancy Hardening
- [ ] `POST /v1/orgs` — creates org schema, seeds default prompts, returns org JWT
- [ ] Tier enforcement: Solopreneur = 1 run, Startup = 5
- [ ] `GET /v1/llmops/cost?org_id=...`
- [ ] Integration test: two orgs cannot read each other's runs

#### S4.4 — CI/CD Pipeline
- [ ] `.github/workflows/ci.yml` — ruff + mypy + pytest + tsc + eslint
- [ ] `.github/workflows/security.yml` — Trivy + Gitleaks on PR
- [ ] `.github/workflows/deploy-staging.yml` — Docker build → ECR → ECS task def update
- [ ] `backend/Dockerfile` — multi-stage, Python 3.12-slim

#### S4.5 — Load Test
- [ ] Locust: 10 concurrent idea submissions
- [ ] P95 pillar1 < 1800s; P95 `/health` < 100ms
- [ ] Redis cache hit rate > 60% on repeated similar ideas

---

## Layer-to-Sprint Matrix

| Layer | Sprint 0 | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 |
|---|---|---|---|---|---|
| 1. Input | ○ | ● | | | |
| 2. Orchestration | | ● | ● | | |
| 3. Agents | | | ● | | |
| 4. Models | | | ● | | |
| 5. Data & Knowledge | ● | ● | ● | | |
| 6. Output | | | | ● | |
| 7. Service & Integration | | | ● | | ● |
| 8. Guardrails | | ● | | | ● |
| 9. Compliance | | | | | ● |
| 10. Observability | ● | | | | ● |

● = primary work, ○ = scaffold only

---

## File Creation Order (exact sequence for backend)

```
backend/app/          (historical: shown as backend/src/autofounder_ai/)
│
├── __init__.py
├── core/
│   ├── config.py            # env var loading (pydantic-settings)
│   ├── udal.py              # Unified Data Access Layer
│   ├── models.py            # SQLAlchemy ORM models
│   ├── vector.py            # pgvector helpers
│   ├── redis_keys.py        # Redis key constants
│   ├── kafka.py             # Confluent Kafka producer/consumer
│   └── telemetry.py         # OTel + Prometheus + logger factory
│
├── api/
│   ├── main.py              # FastAPI app
│   ├── middleware/
│   │   ├── auth.py
│   │   └── rate_limit.py
│   └── routers/
│       ├── health.py
│       ├── ideas.py
│       ├── runs.py
│       └── gates.py
│
├── orchestrator/
│   ├── graph.py             # LangGraph StateGraph
│   ├── task_router.py       # Kafka → agent dispatch
│   └── hitl.py              # HITL gate pause/resume
│
├── guardrails/
│   ├── pipeline.py          # 6-stage runner
│   ├── input.py
│   ├── execution.py
│   └── output.py
│
├── models/
│   ├── llm.py               # LiteLLM + Gemini wrapper
│   └── embeddings.py        # gemini-embedding-2
│
├── prompts/
│   ├── loader.py
│   └── templates/
│       ├── strategy/
│       └── research/
│
├── tools/
│   ├── base.py
│   ├── tavily.py
│   └── serpapi.py
│
└── agents/
    ├── base.py              # Agent ABC
    ├── research/
    │   └── agent.py
    ├── strategy/
    │   └── agent.py
    └── product_planner/
        └── agent.py
```

---

## Key Decisions (Locked)

| Decision | Locked Choice |
|---|---|
| Compute | AWS ECS Fargate (NOT GCP Cloud Run — stack.md is stale) |
| Folder layout | `backend` + `frontend` (incl. `/admin` route group) + `mobile-app` + `infra` + `packages/{shared,api-client}` (lowercase dirs) |
| Backend structure | One consolidated `backend/app/` (api · orchestrator · agents · workers); split in Phase 4 if needed |
| LLM Primary | Gemini 3.5 Flash via LiteLLM |
| Embeddings | `gemini-embedding-2` |
| Vector store | Supabase pgvector |
| Tenant isolation | Schema-per-org + RLS |
| Agent framework | LangGraph (stateful DAG) |
| Backend | FastAPI + Python 3.12 + uv |
| Frontend | Next.js 14 + Tailwind + shadcn/ui (in `frontend/`) |
| Message bus | Confluent Kafka + EventBridge + SQS |
| DB access | UDAL only — no direct SQLAlchemy in agents |
| Auth | Supabase Auth |
| IaC | Terraform (AWS ECS) |
| Package mgr (JS) | pnpm + Turborepo |
| Package mgr (Py) | uv |

---

## Done Definition (Phase 1 complete)

- [ ] `POST /v1/ideas` accepts text idea and returns `run_id` in < 500ms
- [ ] Strategy Agent completes in < 30 min: Lean Canvas + Viability Score + 3 ICPs
- [ ] Product Planner Agent produces PRD + feature list after gate approval
- [ ] Founder Portal shows live progress and Validation Studio
- [ ] HITL gate approve/pivot works from UI
- [ ] All agent outputs pass guardrail pipeline (no raw user text reaches LLM without PII check)
- [ ] Two orgs cannot see each other's data (integration test)
- [ ] `ruff` + `mypy` + `pytest` + `eslint` + `tsc` all pass in CI
- [ ] 10 pilot clients running successfully
- [ ] Cost per run tracked in `cost_ledger` and visible at `/v1/llmops/cost`

---

## Risk Register

| Risk | Probability | Mitigation |
|---|---|---|
| Tavily/SerpAPI rate limits | Medium | Backoff + 1h Redis result cache |
| Gemini latency > 30min SLA | Medium | Stream responses; show partial canvas; alert at 20min |
| Supabase schema-per-tenant connection limit | Low | PgBouncer / Supabase built-in pooling |
| LangGraph checkpoint conflicts | Low | Redis key per `run_id`; Postgres row-level lock |
| Kafka ordering for gate events | Low | Partition by `run_id` |
| PII in LangSmith traces | Medium | Redact before logging; no-log mode initially |
| Kafka creds in `.env.example` | High | Rotate immediately if repo goes public |

---

## Next Action

**S0.1** done (workspace + pyproject fix). Start **S0.2 — Data Layer**:
1. `cd backend && uv add alembic psycopg2-binary python-dotenv`
2. Run `alembic init alembic` inside `backend/`
3. Write migration 001 for platform schema
4. Start `supabase start` locally and run `alembic upgrade head`
