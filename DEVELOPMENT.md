# AutoFounder AI — Development Log

> Running log of what is being built, what is done, and what is next.
> Updated after each completed task.

---

## Session: 2026-06-04

**Developer:** Somesh Chitranshi
**Branch:** `somesh-feature`
**Last Updated:** 2026-06-04 16:49

---

## What We Are Building

AutoFounder AI is a multi-tenant agentic AI SaaS platform that converts a single text idea into a fully validated, designed, built, tested, deployed, marketed, and continuously-improved software business — autonomously.

The platform runs on:
- **Backend:** FastAPI + LangGraph (Python, uv)
- **Database:** Supabase (PostgreSQL 16 + pgvector + Auth + Realtime)
- **Cache:** Redis 7
- **Cloud:** AWS ECS Fargate (multi-AZ)
- **Frontend:** Next.js 14
- **Mobile:** Expo (React Native)

---

## Build Progress

### Phase 1 — Monorepo & Boilerplate ✅ COMPLETE

All 11 tasks done. Workspace tooling, Docker, linting, scripts, and per-component scaffolds in place.

---

### Phase 2 — Infrastructure & Cloud ❌ NOT STARTED

Terraform modules, Supabase setup, CI/CD pipeline, observability baseline.
Owner: Asit. Blocked on: nothing — can start now.

---

### Phase 3 — Backend (FastAPI + LangGraph + Agents) 🔄 IN PROGRESS

#### 3a — Core API & Data Layer

| Task | Description | Status | Completed |
|------|-------------|--------|-----------|
| AF-025 | Alembic migration — `platform` schema (tenants, model_registry, prompt_registry, tool_registry, audit_log, tenant_api_keys) | ✅ Done | 2026-06-04 |
| AF-026 | Alembic migration — per-tenant `org_{uuid}` schema + orchestrator schema | ✅ Done | 2026-06-04 |
| AF-027 | UDAL — unified data access layer (`relational`, `vector`, `graph`, `object`) | ✅ Done | 2026-06-04 |
| AF-028 | FastAPI app bootstrap — lifespan, DI, exception handler, CORS | ✅ Done | 2026-06-04 |
| AF-029 | Auth middleware — Supabase JWT, OPA, OrgContext, mTLS | ✅ Done | 2026-06-04 |
| AF-030 | REST API endpoints — ideas, runs, gates, artifacts, feedback, cost | ✅ Done | 2026-06-04 |
| AF-031 | Supabase Realtime integration — step_events pg_notify | ✅ Done | 2026-06-04 |
| AF-032 | Redis integration — session cache, checkpoints, prompt cache, cost accumulator | ✅ Done | 2026-06-06 |

#### 3b — LangGraph Orchestration ✅ COMPLETE

| Task | Description | Status | Completed |
|------|-------------|--------|-----------|
| AF-033 | LangGraph orchestration engine — StateGraph factory + OrchestratorEngine persistence | ✅ Done | 2026-06-06 |
| AF-034 | HITL gate manager — dynamic gate creation, transitions, notifications, timeouts | ✅ Done | 2026-06-06 |
| AF-035 | SQS worker loop — multi-queue polling, gRPC step dispatching, event stream database logging, retry visibility backoff | ✅ Done | 2026-06-06 |

#### 3c — AI Agents ❌ NOT STARTED
#### 3d — Guardrails, Tools & Prompts ❌ NOT STARTED

---

### Phase 4 — Frontend (Next.js 14) ❌ NOT STARTED
### Phase 5 — Mobile (Expo React Native) ❌ NOT STARTED
### Phase 6 — VS Code Extension ❌ NOT STARTED

---

## AF-025 — Detail Log

**Task:** Alembic migration for `platform` schema
**Branch:** `somesh-feature`
**Completed:** 2026-06-04 16:49

### What was found
- `platform` schema already existed in Supabase (created manually, no Alembic tracking)
- Tables present: `tenants`, `model_registry`, `prompt_registry`, `tool_registry`, `audit_log`, `tenant_api_keys`
- No `alembic_version` table existed — Alembic had never been run against this DB
- Per-tenant tables (`runs`, `artifacts`, `gates`, etc.) existed in `public` schema (wrong — should be `org_{uuid}`)

### What was built
- `backend/alembic/versions/20260604_0001_0002_platform_schema.py`
  - `CREATE SCHEMA IF NOT EXISTS platform`
  - `platform.tenants` — org billing entity with tier + status + RLS
  - `platform.tenant_api_keys` — hashed API keys per tenant
  - `platform.model_registry` — LLM models, routing config, cost/token
  - `platform.prompt_registry` — versioned Jinja2 templates, canary support
  - `platform.tool_registry` — MCP tool definitions, rate limits
  - `platform.audit_log` — immutable append-only compliance trail (UPDATE/DELETE blocked via rules)
  - RLS enabled on all tables
  - Indexes on all FK and hot-query columns
  - Full `downgrade()` implemented

### How it was applied
```bash
# Stamp DB at 0001_initial (existing tables, no alembic_version)
DATABASE_URL=postgresql+asyncpg://... alembic stamp 0001_initial

# Apply AF-025 migration
DATABASE_URL=postgresql+asyncpg://... alembic upgrade head
# Result: 0002_platform_schema (head)
```

### Known issue found (not AF-025 scope)
- `backend/.env` does not exist — `config.py` looks for `.env` relative to `backend/` dir
- Root `.env` `DATABASE_URL` missing `+asyncpg` driver prefix
- Fix belongs in AF-028 (FastAPI bootstrap)

---

---

## AF-026 — Detail Log

**Task:** Alembic migration — per-tenant schema + orchestrator checkpoints
**Branch:** `somesh-feature`
**Completed:** 2026-06-04

### What was built
- `backend/alembic/versions/20260604_0002_0003_tenant_schema.py`
  - `CREATE EXTENSION IF NOT EXISTS vector` (pgvector for embeddings)
  - `orchestrator` schema + `orchestrator.checkpoints` table — LangGraph hot checkpoint persistence; PK `(run_id, checkpoint_ns, checkpoint_id)`
  - `provision_org_schema(org_id TEXT)` PL/pgSQL function — called by UDAL at org signup; creates `org_{uuid}` schema with all 7 per-tenant tables:
    - `workspaces` — org project scope
    - `runs` — pipeline execution state (status, current_pillar, cost_usd)
    - `artifacts` — generated outputs (lean_canvas, erd, repo_url, deploy_url, etc.)
    - `gates` — HITL checkpoints (pending/approved/rejected/timed_out); partial index on pending state
    - `step_events` — append-only agent log; UPDATE/DELETE blocked via rules; pg_notify trigger feeds Supabase Realtime (AF-031)
    - `memory_episodes` — episodic memory with `vector(768)` embedding + IVFFlat ANN index (cosine, 100 lists)
    - `cost_ledger` — per-model token billing (input_tokens, output_tokens, cost_usd)
  - RLS enabled + `org_isolation` policy on all 7 tables
  - Indexes on all FK + hot-query columns
  - Full `downgrade()` implemented

### How to apply
```bash
DATABASE_URL=postgresql+asyncpg://... alembic upgrade head
# Result: 0003_tenant_schema (head)

# Provision a new org at runtime:
# SELECT provision_org_schema('a1b2c3d4-...');
```

---

## AF-029 — Detail Log

**Task:** Auth middleware — Supabase JWT, OPA, OrgContext, mTLS
**Branch:** `somesh-feature`
**Completed:** 2026-06-04

### What was built
- Added `pyjwt>=2.8.0` to backend dependencies.
- Added `supabase_jwt_secret`, `opa_url`, and `mtls` configurations to `Settings` in `app/core/config.py`.
- Refactored `Principal` to hold scopes, and implemented signature-verified `verify_jwt` and proxy-header `verify_mtls` in `app/core/security.py`.
- Built async OPA client query utility (`check_opa_policy`) in `app/guardrails/opa.py` and base Rego authorization rules in `app/guardrails/opa/policies/agent_policy.rego`.
- Implemented generator-based `get_principal` in `app/api/deps.py` managing ContextVar tenant isolation (`set_tenant_context` / `reset_tenant_context`) per request lifetime, matching the spec's dependency injection path.
- Created `tests/test_auth.py` verifying JWT claim decoding, dev mode fallbacks, OPA rule checks, and ContextVar scoping.

### Verification status
- All 11 unit & integration tests passed.
- Entire test suite (58 tests) passed.
- `mypy` static type checking clean.
- `ruff` linter checks passed.

---

## AF-032 — Detail Log

**Task:** Redis integration — session cache, checkpoints, prompt cache, cost accumulator
**Branch:** `somesh-feature`
**Completed:** 2026-06-06

### What was built
- Implemented `CacheClient` (`backend/app/db/cache.py`) supporting tenant-prefixed Redis keys (`org:{org_id}:*`) to enforce isolation.
- Built helper functions for caching LLM prompts and accumulative token/dollar costs.
- Added comprehensive unit testing suite in `backend/tests/db/test_cache.py`.

---

## AF-033 — Detail Log

**Task:** LangGraph orchestration engine — StateGraph factory + OrchestratorEngine persistence
**Branch:** `somesh-feature`
**Completed:** 2026-06-06

### What was built
- Defined unified LangGraph state `RunState` and initialization schema.
- Built the 7-pillar `StateGraph` in `backend/app/orchestrator/graph.py` containing nodes, conditional routing edges, and interrupt checkpointers.
- Designed `DualCheckpointer` syncing execution frames durably to Postgres + Redis hot-caching.
- Implemented `OrchestratorEngine` driving the run lifecycle.

---

## AF-034 — Detail Log

**Task:** HITL gate manager — dynamic gate creation, transitions, notifications, timeouts
**Branch:** `somesh-feature`
**Completed:** 2026-06-06

### What was built
- Implemented the HITL gate manager (`backend/app/orchestrator/hitl/gate_manager.py`) creating and managing approval gates.
- Built SQS Gate Decision Consumer (`backend/app/orchestrator/events/consumer.py`) handling asynchronous run resumption.
- Integrated EventBridge event producer (`backend/app/orchestrator/events/producer.py`) publishing platform messages.

---

## AF-035 — Detail Log

**Task:** SQS worker loop — multi-queue polling, gRPC step dispatching, event stream database logging, retry visibility backoff
**Branch:** `somesh-feature`
**Completed:** 2026-06-06

### What was built
- Created `SQSPillarWorker` managing concurrent polling threads per execution pillar (real SQS + local in-memory fallback).
- Wired gRPC dispatch stream calling the Agent Worker service `DispatchStep` endpoint, logging event streams to the DB `step_events` table under RLS, and resuming the engine.
- Added retry backoff with jitter and EventBridge DLQ escalation.

---

## Next Up

| Task | Description | Owner |
|------|-------------|-------|
| AF-036 | BaseAgent ABC — understand, plan, execute, verify, learn agent baseline interface | Asit |


## Notes

- Always run Alembic with `DATABASE_URL=postgresql+asyncpg://...` prefix until AF-028 fixes `backend/.env`
- `platform` schema = shared cross-tenant config. `org_{uuid}` schema = per-customer data silo
- Supabase project ref: `geuuatjsmtsunwxnfidt` | Region: `ap-south-1` (Mumbai)
