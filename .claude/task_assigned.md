# AutoFounder AI — Task Assignment (Single Source of Truth)

> **AutoFounder AI** is a multi-tenant agentic AI SaaS platform that converts a single text idea into a fully validated, designed, built, tested, deployed, and marketed software business — autonomously, in days instead of months.
>
> **📌 This is the ONLY file the team needs to refer to.** It merges the full 78-task plan (every feature, branch, and status from `TASKS.md`) **+** who owns what **+** what each person can start *right now* **+** what is *blocked and by whom* **+** what is *missing / unassigned*. You do **not** need to open `TASKS.md`, `PLAN.md`, or `CLAUDE.md` to work from this.
>
> **Date**: 2026-06-01 · **Phase**: 1 — Validation Engine · **Target**: 10 pilot clients
> **Assigned by**: Asit Piri (Project Lead) · **Current reality**: Phase 1 ✅ done · Phase 2 ❌ not started.

---

## How to read this file (plain-language legend)

Think of the project like building a house. You can't paint a room (build your agent) until the walls and wiring (the shared platform) exist. But you **can** buy the paint and design the colour scheme today. That "do it now, before the house is wired" work is the **independent** work each person should start immediately.

**Status (is the task built yet?)**

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed |
| ❌ | Pending |

**Start-readiness (can the owner begin *now*?)**

| Symbol | Meaning |
|--------|---------|
| 🟢 **Now** | No blocker. Depends only on already-done work. Begin today. |
| 🟡 **Partly now** | You can do the *offline* half today (prompts, schemas, tools, tests, UI mockups). The *wired* half waits for the platform. |
| 🔴 **Blocked** | Cannot meaningfully start until a listed dependency lands. |
| ⚪ **No owner** | A real task with **nobody assigned** — see [Part D — What's Missing](#part-d--whats-missing-gaps--unassigned). |

**The one rule that explains every dependency:** every agent (Pillars 1–7) needs the **shared backend foundation** first — `UDAL` (AF-027), `BaseAgent` (AF-036), the LLM Router + Prompt Registry + Guardrails (AF-046–049), and the Orchestrator (AF-033). Until those land, agent owners build everything *around* their agent but cannot ship a *running* one.

---

## Team Roster → Ownership

| # | Member | Area | Owns (AF-IDs) |
|---|--------|------|---------------|
| 1 | **Asit Piri** (Lead) | Platform foundation: PRD, Architecture, GitHub, CI/CD, DB, APIs, AWS, Code Review, Integration & Merging · **+ Guardrails · VS Code Extension · Finance & Ops/Risk** | AF-012 → AF-031, AF-036, AF-046, AF-047, AF-072 → AF-078 |
| 2 | **Somesh Chitranshi** | Pillar 1 — Idea Validation & Market Research | AF-025 → AF-035, AF-037 → AF-039 |
| 3 | **Kaushlendra Kumar Gupta** | Pillar 2 — Architecture & Tech Stack Design | AF-040 |
| 4 | **Kartik Mogalapalli** | Pillar 3 — Autonomous Code Generation | AF-041 |
| 5 | **Vishal Prasad** | Pillar 4 — Testing & Self-Healing | AF-042 |
| 6 | **Prasenjit Roy** | Pillar 5 — Deployment & Infrastructure | AF-043 |
| 7 | **Pallavi Anil Sindkar** | Pillar 6 — Marketing & Launch Automation | AF-044 |
| 8 | **Purnima** | Pillar 7 — LLMOps & Continuous Learning (+ shared prompt/router/eval) | AF-045, AF-048, AF-049, AF-050 |
| 9 | **Raunak Ravi** | Web Interface Design | AF-051 → AF-062 |
| 10 | **Yogesh Raut** | Mobile Interface Design | AF-063 → AF-071 |
| — | ✅ **All assigned** | _(VS Code Extension · Guardrails pipeline · Finance & Ops/Risk agents are now owned by **Asit** — folded into row 1)_ | — |

---

## Status Overview

| Phase | Description | Lead Owner(s) | Total | ✅ Done | ❌ Pending |
|-------|-------------|---------------|-------|---------|-----------|
| Phase 1 | Monorepo & Boilerplate Setup | Team | 11 | 11 | 0 |
| Phase 2 | Infrastructure & Cloud | Asit (Vishal exec) | 13 | 6 | 7 |
| Phase 3 | Backend — FastAPI + Agents | Asit (3a/3b + 3d guardrails/tools) + all Pillar owners (3c) + Purnima (3d prompts/router/eval) | 26 | 11 | 15 |
| Phase 4 | Frontend — Next.js 14 | Raunak | 12 | 0 | 12 |
| Phase 5 | Mobile — Expo React Native | Yogesh | 9 | 0 | 9 |
| Phase 6 | VS Code Extension | **Asit** | 7 | 0 | 7 |
| **Total** | | | **78** | **28** | **50** |

**Per-person task count:** Asit **24** · Somesh 3 · Kaushlendra 1 · Kartik 1 · Vishal 1 · Prasenjit 1 · Pallavi 1 · Purnima 4 · Raunak 12 · Yogesh 9 · **Unassigned 0** _(AF-046 Guardrails + AF-072→AF-078 VS Code reassigned to Asit; Finance & Ops/Risk agents also owned by Asit, Phase 4)_ = 56 pending + 22 done = **78**.


---

# PART A — Master Task List (by Phase)

> Full feature descriptions merged from `TASKS.md`, now with **Owner**, **Depends on**, and **Start** columns. This is the complete plan — a superset of `TASKS.md`.

## Phase 1 — Monorepo & Boilerplate Setup ✅ COMPLETE

> Foundation: workspace tooling, Docker, linting, scripts, and per-component scaffolds. **All 11 tasks done.**

| ID | Owner | Task | Branch | Status |
|----|-------|------|--------|--------|
| AF-001 | Team | Init pnpm workspace (`pnpm-workspace.yaml`) + Turborepo (`turbo.json`) with `dev`, `lint`, `build` pipelines | `feature/monorepo-init` | ✅ |
| AF-002 | Team | Root `package.json` — `turbo dev`, unified `lint`, `format:check` scripts wiring Ruff + ESLint | `feature/root-scripts` | ✅ |
| AF-003 | Team | `docker-compose.yml` — Redis 7 (AOF persistence) with named volumes; Supabase CLI manages PostgreSQL + pgvector + Auth + Storage + Realtime locally via `supabase start` | `feature/docker-compose-setup` | ✅ |
| AF-004 | Team | Backend scaffold — `backend/` with `pyproject.toml`, `uv.lock`, Ruff + mypy + pytest, `app/` layout, Alembic, `Dockerfile` | `feature/backend-scaffold` | ✅ |
| AF-005 | Team | Frontend scaffold — `frontend/` TypeScript + React placeholder, `tsconfig.json`, `package.json` | `feature/frontend-scaffold` | ✅ |
| AF-006 | Team | Mobile scaffold — `mobile-app/` Expo + TypeScript placeholder | `feature/mobile-scaffold` | ✅ |
| AF-007 | Team | VS Code Extension scaffold — `vscode-extension/` TypeScript placeholder | `feature/vscode-extension-scaffold` | ✅ |
| AF-008 | Team | ESLint v9 flat config (`eslint.config.mjs`) + Prettier — shared rules across all JS/TS workspaces | `feature/lint-config` | ✅ |
| AF-009 | Team | `Makefile` — `install`, `stack`, `stack-down`, `dev`, `backend-lint`, `js-lint`, `quality` targets | `feature/makefile-scripts` | ✅ |
| AF-010 | Team | `scripts/setup-dev.sh` + `scripts/setup-dev.ps1` — cross-platform one-command local environment setup | `feature/dev-setup-scripts` | ✅ |
| AF-011 | Team | `.env.example` + `README.md` — env var documentation and project onboarding guide | `feature/env-and-readme` | ✅ |

## Phase 2 — Infrastructure & Cloud 🟢 (Owner: Asit — can start now)

> AWS networking, ECS services, managed databases, messaging, CI/CD pipeline, and observability baseline. **Depends on: Phase 1 (done) → unblocked.**
>
> **Progress (2026-06-06, Vishal):** ✅ `AF-012` networking, `AF-013` ecs, `AF-018` alb (*ALB+WAFv2; CloudFront/Shield deferred), `AF-019` iam, `AF-020` secrets, `AF-021` ecr — built + `terraform validate`-clean on branch `feat/infra/terraform-networking` (pending PR → `dev`). ECR lives in a new account-global stack `infra/terraform/global/`. **Remaining:** AF-014 Supabase, AF-015 ElastiCache, AF-016 S3, AF-017 messaging, AF-022 CI/CD (CI done, CD pending), AF-023 OTel (JSON logs done), AF-024 Prometheus/Grafana.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-012 | Asit→Vishal | Terraform module `networking` — VPC, public/private subnets (Multi-AZ), NAT gateways, VPC endpoints for S3/ECR/Secrets | `feature/terraform-networking` | Phase 1 | 🟢 | ✅ |
| AF-013 | Asit→Vishal | Terraform module `ecs` — ECS Fargate cluster, task definitions per service, auto-scaling target-tracking policies | `feature/terraform-ecs` | AF-012 | 🟢 | ✅ |
| AF-014 | Asit | Supabase project setup — `supabase link`, RLS policies, pgvector extension, schema-per-tenant migrations (hosted; no RDS) | `feature/supabase-setup` | Phase 1 | 🟢 | ❌ |
| AF-015 | Asit | Terraform module `elasticache` — Redis 7 cluster (Multi-AZ), subnet groups, auth token | `feature/terraform-elasticache` | AF-012 | 🟢 | ❌ |
| AF-016 | Asit | Terraform module `s3` — artifacts bucket, RLHF data lake, prompt-templates bucket; S3 Object Lock on audit bucket (7 yr) | `feature/terraform-s3` | AF-012 | 🟢 | ❌ |
| AF-017 | Asit | Terraform module `messaging` — Confluent Kafka (primary bus + LLMOps telemetry), EventBridge bus + rules, per-pillar SQS queues + DLQs, SNS topic | `feature/terraform-messaging` | AF-012 | 🟢 | ❌ |
| AF-018 | Asit→Vishal | Terraform module `alb` — Application Load Balancer (L7), HTTPS listener, target groups per ECS service; CloudFront + WAF + Shield | `feature/terraform-alb` | AF-013 | 🟡 | ✅* |
| AF-019 | Asit→Vishal | Terraform module `iam` — least-privilege task execution roles per ECS service, no wildcard `*:*` policies | `feature/terraform-iam` | AF-012 | 🟢 | ✅ |
| AF-020 | Asit→Vishal | Terraform module `secrets` — Secrets Manager entries + SSM Parameter Store hierarchy; KMS CMK for encryption at rest | `feature/terraform-secrets` | AF-012 | 🟢 | ✅ |
| AF-021 | Asit→Vishal | Terraform module `ecr` — one ECR repo per service, image scanning on push, lifecycle policies | `feature/terraform-ecr` | Phase 1 | 🟢 | ✅ |
| AF-022 | Asit | GitHub Actions — `ci.yml` (lint, typecheck, unit, integration, security scans), `deploy-staging.yml`, `deploy-prod.yml` (canary ramp); ECR push + CodeDeploy blue/green | `feature/cicd-pipeline` | AF-021 | 🟡 | ❌ |
| AF-023 | Asit (← Purnima support) | OpenTelemetry baseline — OTel SDK in backend (FastAPI), structured JSON logs (`trace_id · organization_id · run_id · agent_id · model · env`), Fluent Bit → CloudWatch | `feature/observability-baseline` | AF-028 | 🟡 | ❌ |
| AF-024 | Asit (← Purnima support) | Prometheus + Grafana — metrics endpoint on all services, RED + USE dashboards, per-tenant cost panel; LangSmith project wired | `feature/metrics-dashboards` | AF-023 | 🟡 | ❌ |

## Phase 3 — Backend (FastAPI + LangGraph + Agents)

> Core API, orchestration engine, all AI agents, guardrails, tool/prompt registries, and RAG pipeline. **Depends on: Phase 2.**

### 3a — Core API & Data Layer 🟢/🟡 (Owner: Asit)

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-025 | Somesh | Alembic migrations — `platform` schema (tenants, model_registry, prompt_registry, tool_registry, audit_log) | `feature/db-migrations-platform` | AF-014 | 🟢 | ✅ |
| AF-026 | Somesh | Alembic migrations — per-tenant schema (runs, artifacts, gates, step_events, memory_episodes, cost_ledger) + orchestrator schema (checkpoints) | `feature/db-migrations-tenant` | AF-025 | 🟢 | ✅ |
| AF-027 | Somesh | **⭐ UDAL** — `backend/app/db/` client: `relational()`, `vector()`, `graph()`, `object()`; `contextvars` tenant propagation, cross-tenant guard (SEV-1 on breach), lineage audit emit | `feature/udal-core` | AF-026 | 🟢 | ✅ |
| AF-028 | Somesh | FastAPI app bootstrap — lifespan, DI, global exception handler (`{code, message, requestId}`), CORS | `feature/fastapi-app-setup` | AF-027 | 🟡 | ✅ |
| AF-029 | Somesh | Auth middleware — Supabase JWT validation (`SUPABASE_JWT_SECRET`), OPA policy sidecar, `OrgContext` via `contextvars`, mTLS service-to-service | `feature/auth-middleware` | AF-028 | 🟢 | ✅ |
| AF-030 | Somesh | **⭐ REST endpoints** — `POST /v1/ideas`, `GET /v1/runs/{id}`, `POST /v1/runs/{id}/gates/{gate_id}`, `GET /v1/runs/{id}/artifacts`, `POST /v1/feedback`, `GET /v1/llmops/cost`; OpenAPI 3.1 spec | `feature/rest-api-endpoints` | AF-028 | 🟢 | ✅ |
| AF-031 | Somesh | Supabase Realtime — subscribe to `step_events` changes (pg_notify); frontend uses `@supabase/supabase-js` channel; reconnect replay from `step_events` | `feature/realtime-integration` | AF-026 | 🟡 | ✅ |
| AF-032 | Somesh | Redis integration — session cache, LangGraph plan checkpoints, semantic prompt cache (`llm:prompt_cache:{sha256}`), embedding cache, per-tenant cost accumulator | `feature/redis-integration` | AF-015, AF-028 | 🟢 | ✅ |

### 3b — LangGraph Orchestration 🟢 (Owner: Somesh)

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-033 | Somesh | **⭐ `RunState` TypedDict + `StateGraph` factory** — nodes per pillar step, conditional edges, checkpointing to Postgres + Redis after every node | `feature/langgraph-graph` | AF-027, AF-032 | 🟢 | ✅ |
| AF-034 | Somesh | HITL gate state machine — `pending → approved / rejected / timed_out`; EventBridge `gate.required` emit; SQS consumer for gate decisions | `feature/hitl-gate-manager` | AF-033, AF-017 | 🟢 | ✅ |
| AF-035 | Somesh | SQS worker loop — poll per-pillar queues, deserialise step, dispatch to agent runner, exponential backoff + jitter, DLQ escalation | `feature/sqs-worker` | AF-017, AF-033 | 🟢 | ✅ |

### 3c — AI Agents (Owners: Pillar leads)

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-036 | **Asit / ⚪ shared** | **⭐ `BaseAgent` ABC** — `understand()`, `plan()`, `execute()`, `verify()`, `learn()`; typed error hierarchy; circuit breakers on LLM + tool calls. **Blocks ALL agents below.** | `feature/base-agent` | AF-027 | 🔴 | ❌ |
| AF-037 | **Somesh** | Strategy & Ideation Agent (Pillar 1) — TAM/SAM/SOM, competitor discovery, persona gen, Lean Canvas, viability 0–100, bias audit, 3 pivots; SLA < 30 min | `feature/strategy-agent` | AF-036, AF-048, AF-049 | 🟡 | ❌ |
| AF-038 | **Somesh** | Research Agent (Pillar 1) — Tavily + SerpAPI + Crunchbase + G2 + SimilarWeb fan-out, synthesis, citation groundedness check | `feature/research-agent` | AF-036, AF-047 | 🟡 | ❌ |
| AF-039 | **Somesh** | Product Planner Agent (Pillar 1.5) — PRD generation, roadmap, user stories, requirements extraction from strategy output | `feature/product-planner-agent` | AF-037 | 🟡 | ❌ |
| AF-040 | **Kaushlendra** | Architect Agent (Pillar 2) — FR/NFR extraction, ERD, OpenAPI contract, stack selection, microservice boundaries, cost forecast; HITL approval gate | `feature/architect-agent` | AF-036, AF-039 | 🟡 | ❌ |
| AF-041 | **Kartik** | Coder Agent (Pillar 3) — Frontend Specialist (Next.js 14 + Tailwind + shadcn/ui) ∥ Backend Specialist (FastAPI + SQLAlchemy + Supabase Auth + Stripe); Alembic migrations; zero lint errors; CI/CD scaffold | `feature/coder-agent` | AF-036, AF-040 | 🟡 | ❌ |
| AF-042 | **Vishal** | Reviewer / Self-Healer Agent (Pillar 4) — static analysis, unit + integration test gen, security scans (Trivy/Semgrep/Snyk), sandbox execution, AST-aware patching, LLM-as-judge; max 5 cycles; coverage ≥ 80% | `feature/reviewer-agent` | AF-036, AF-041 | 🟡 | ❌ |
| AF-043 | **Prasenjit** | DevOps Agent (Pillar 5) — multi-stage Dockerfile, Terraform plan + apply, ECS provisioning, Route 53 + ACM, monitoring setup, smoke test; SLA < 10 min; infra-spend HITL gate | `feature/devops-agent` | AF-036, AF-042 | 🟡 | ❌ |
| AF-044 | **Pallavi** | Marketing Agent (Pillar 6) — brand kit (DALL-E 3), landing page, SEO engine (10 blog drafts), email drip sequences, social posts; feature-list hallucination cross-ref; Launch Control Center HITL gate | `feature/marketing-agent` | AF-036, AF-040 | 🟡 | ❌ |
| AF-045 | **Purnima** | LLMOps Agent (Pillar 7) — trace analysis, DSPy prompt optimisation, Promptfoo regression, LiteLLM routing updates, TruLens drift monitoring, A/B experiments, FinOps report; weekly Step Functions cycle | `feature/llmops-agent` | AF-036, all agents running | 🔴 | ❌ |

### 3d — Guardrails, Tools & Prompts (Owners: Asit [AF-046 Guardrails + AF-047 Tools] + Purnima [AF-048/049/050])

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-046 | **Asit** (Purnima co-owns output/monitoring stages) | **6-stage Guardrails Pipeline** — OPA policy, Presidio PII + Llama Guard input, prompt constraint validators, tool schema + cost-cap execution guard, TruLens + citation output guard, Evidently AI monitoring; immutable audit log. **Wraps every agent call.** | `feature/guardrails-pipeline` | AF-028 | 🟡 | ❌ |
| AF-047 | **Asit** (shell) + all pillars (entries) | Tool Registry + tools — `ToolRegistry` singleton; research tools (Tavily, SerpAPI, Crunchbase, G2); engineering tools (GitHub, Stripe, AWS Pricing API); marketing tools (X, LinkedIn, Resend, ProductHunt) | `feature/tool-registry` | AF-027 | 🟡 | ❌ |
| AF-048 | **Purnima** (shell) + all pillars (prompts) | Prompt Registry — versioned Jinja2 templates in `prompt_registry` table + S3; `get()` resolves active/canary; deterministic canary split; strict variable validation | `feature/prompt-registry` | AF-025 | 🟡 | ❌ |
| AF-049 | **Purnima** | LiteLLM Model Router + RAG — task-class → model routing (Gemini 3.5 Flash; gemini-embedding-2 768-dim); hybrid BM25 + ANN on Supabase pgvector; Cohere reranking; context compression; citation check | `feature/model-router-rag` | AF-027, AF-014 | 🟡 | ❌ |
| AF-050 | **Purnima** + pillar golden sets | Eval harness — Promptfoo golden sets per agent, LangSmith batch eval runner, CI gate blocking prompt promotion on score regression > 2% | `feature/eval-harness` | AF-048 | 🟡 | ❌ |

## Phase 4 — Frontend (Next.js 14) 🟢/🟡 (Owner: Raunak)

> Founder Portal with all 7 pillar surfaces, real-time log streaming, HITL gate UI, admin dashboard. **Depends on: Phase 3 for integration — but every screen can be built on mock data now.**

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-051 | Raunak | Next.js 14 App Router — TypeScript strict, Tailwind, shadcn/ui, Supabase Auth (`@supabase/supabase-js` + `@supabase/ssr`), global error boundary + Sentry | `feature/nextjs-setup` | Phase 1 | 🟢 | ❌ |
| AF-052 | Raunak | Typed API client (`lib/api-client.ts`) + Realtime hook (`lib/realtime-client.ts`) — `useRun()` merging React Query + Supabase Realtime, `useGate()` polling + mutation | `feature/api-client-hooks` | AF-030, AF-031 | 🔴 | ❌ |
| AF-053 | Raunak | Zustand stores + React Query config — `runStore`, `gateStore`, `uiStore`; responsive layout shell with live cost ticker | `feature/state-management` | AF-051 | 🟢 | ❌ |
| AF-054 | Raunak | Idea Intake surface — multi-modal form (text, PDF, voice, URL), locale selector, `POST /v1/ideas`, redirect to run page | `feature/idea-intake-ui` | AF-052 (real) | 🟡 | ❌ |
| AF-055 | Raunak | Validation Studio (Pillar 1) — Lean Canvas viewer, viability gauge 0–100, ICP cards, pivot picker, approve/pivot HITL UI | `feature/validation-studio` | AF-037 (data) | 🟡 | ❌ |
| AF-056 | Raunak | Architecture Studio (Pillar 2) — Mermaid ERD renderer, Swagger UI OpenAPI viewer, stack card, cost forecast, approve/reject HITL UI | `feature/architecture-studio` | AF-040 (data) | 🟡 | ❌ |
| AF-057 | Raunak | Code Review Studio (Pillar 3–4) — Monaco diff viewer, Reviewer comments panel, self-heal cycle progress, security scan results table | `feature/code-review-studio` | AF-042 (data) | 🟡 | ❌ |
| AF-058 | Raunak | Deploy Console (Pillar 5) — live deployment log stream, infra-spend HITL gate, smoke test card, live URL badge, 1-click rollback | `feature/deploy-console` | AF-043 (data) | 🟡 | ❌ |
| AF-059 | Raunak | Launch Control Center (Pillar 6) — brand kit preview, landing page iframe, social post drafts edit-in-place, email sequence preview, approve/edit HITL; nothing publishes without founder sign-off | `feature/launch-control-center` | AF-044 (data) | 🟡 | ❌ |
| AF-060 | Raunak | LLMOps Dashboard (Pillar 7) — cost by model/pillar/run, drift score time-series, eval score history, prompt version table with canary indicator | `feature/llmops-dashboard` | AF-045 (data) | 🟡 | ❌ |
| AF-061 | Raunak | Run List / Dashboard — all runs with status, pillar, cost, created date; filter + search; skeleton loaders | `feature/run-dashboard` | AF-030 | 🟡 | ❌ |
| AF-062 | Raunak | Admin Dashboard — tenant CRUD, model registry mgmt, prompt registry lifecycle, tool registry, audit log viewer, platform FinOps view ⚠️ *(large — flag if too much)* | `feature/admin-dashboard` | AF-030 | 🟡 | ❌ |

## Phase 5 — Mobile (Expo React Native) 🟢/🟡 (Owner: Yogesh)

> Founder-on-the-go: idea submission, run monitoring, live HITL gate approvals, push notifications. **Depends on: Phase 3 for integration — screens buildable on mock data now.**

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-063 | Yogesh | Expo Router scaffold — TS strict, Supabase Auth (`@supabase/supabase-js` + `ExpoSecureStoreAdapter`), secure token storage in `expo-secure-store`, shared API client from `packages/api-client` | `feature/expo-setup` | Phase 1 | 🟢 | ❌ |
| AF-064 | Yogesh | Push notifications — Expo Push → SNS → realtime; deep-link on tap to gate or run screen | `feature/push-notifications` | AF-017 (SNS) | 🔴 | ❌ |
| AF-065 | Yogesh | Idea Intake screen — text input, voice record (Expo AV), file attach; submit to `POST /v1/ideas` | `feature/mobile-idea-intake` | AF-030 | 🟡 | ❌ |
| AF-066 | Yogesh | Run Dashboard screen — live run list with status badges + cost; pull-to-refresh; realtime updates | `feature/mobile-run-dashboard` | AF-030, AF-031 | 🟡 | ❌ |
| AF-067 | Yogesh | Run Detail screen — current pillar progress, step log stream, active gate banner | `feature/mobile-run-detail` | AF-031 | 🟡 | ❌ |
| AF-068 | Yogesh | HITL Gate Approval screens — gate-specific review UI (Lean Canvas, Architecture summary, Launch preview); approve/reject with note; offline queue + sync on reconnect | `feature/mobile-gate-approval` | AF-034 | 🟡 | ❌ |
| AF-069 | Yogesh | Artifacts Viewer — browse outputs (canvas, ERD image, live URL, brand kit, social posts) | `feature/mobile-artifacts-viewer` | AF-030 | 🟡 | ❌ |
| AF-070 | Yogesh | LLMOps Summary screen — cost card, eval score card, last drift check; dark/light mode following system | `feature/mobile-llmops-summary` | AF-045 (data) | 🟡 | ❌ |
| AF-071 | Yogesh | EAS Build + release — `eas.json` profiles (development, preview, production); App Store + Google Play submit via `eas submit` | `feature/eas-build-pipeline` | AF-063 | 🟢 | ❌ |

## Phase 6 — VS Code Extension 🟢 (Owner: Asit — Depends on: Phase 3)

> In-editor AI co-founder: run monitoring, HITL gate approvals, code-gen commands. **Owner: Asit** (reassigned 2026-06-04 from unassigned). AF-072 is 🟢 now; the rest depend on Phase 3. Plan: `developer-plans/12-asit-vscode-extension-plan.md`.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-072 | Asit | Extension core — activation event, command palette scaffold, `ExtensionContext` lifecycle, Supabase Auth PKCE flow with token in `SecretStorage` | `feature/vscode-extension-core` | Phase 1 | 🟢 | ❌ |
| AF-073 | Asit | Sidebar tree view — run list with status icons, pillar progress, live cost badge; refreshes via WebSocket | `feature/vscode-sidebar` | AF-030, AF-031 | 🔴 | ❌ |
| AF-074 | Asit | HITL gate notifications — VS Code banner on `gate.required`; inline approve/reject buttons | `feature/vscode-gate-notifications` | AF-034 | 🔴 | ❌ |
| AF-075 | Asit | Code-gen commands — `Generate Component`, `Generate API Endpoint`; invokes Coder Agent, streams tokens into editor tab | `feature/vscode-code-gen` | AF-041 | 🔴 | ❌ |
| AF-076 | Asit | Live token streaming panel — `WebviewPanel` rendering agent step log stream in real time; follows active run | `feature/vscode-streaming-panel` | AF-031 | 🔴 | ❌ |
| AF-077 | Asit | Artifact quick-open — `Open Lean Canvas`, `Open ERD`, `Open OpenAPI spec`; fetches `GET /v1/runs/{id}/artifacts`, previews in editor | `feature/vscode-artifact-viewer` | AF-030 | 🔴 | ❌ |
| AF-078 | Asit | Marketplace packaging — `vsce package`, `vsce publish` in GitHub Actions; auto-bump version on merge to `main` | `feature/vscode-publish` | AF-072 | 🟡 | ❌ |

---

# PART B — Task List (by Person)

> Each person's full scope, what to start **today**, and what they're blocked on. The "🟢 Do today" items need **no platform** — start now so you're ready the moment the foundation lands.

## 1. Asit Piri — Lead / Platform Foundation 🟢 START NOW (critical path)

> **You are the unblocker.** Every "wired" task on the team waits on you. Your speed = the team's speed.

**Owns (28 tasks):** AF-012 → AF-024 (all infra) · AF-036 (BaseAgent) · AF-047 (tool registry shell) · **AF-046 (Guardrails pipeline — Purnima co-owns output/monitoring)** · **AF-072 → AF-078 (VS Code Extension, Phase 6)** · **Finance & Ops/Risk agents (Phase 4, design deferred)**.

> ⚠️ **Overload note (bus-factor 1):** folding the previously-unassigned work (Guardrails, VS Code Extension, Finance & Ops/Risk) into Asit raises an already-overloaded lead to **~32 tasks** gating 9 people. **Strongly recommend delegating** the orchestrator (AF-033–035), BaseAgent (AF-036), or the entire VS Code Extension (AF-072–078) to an early-finishing pillar owner. Detailed plans: `developer-plans/11-asit-guardrails-pipeline-plan.md`, `12-asit-vscode-extension-plan.md`, `13-asit-finance-ops-risk-plan.md`.

_Phase 2 — Infrastructure & Cloud_

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-012 | Asit→Vishal | Terraform module `networking` — VPC, public/private subnets (Multi-AZ), NAT gateways, VPC endpoints for S3/ECR/Secrets | `feature/terraform-networking` | Phase 1 | 🟢 | ✅ |
| AF-013 | Asit→Vishal | Terraform module `ecs` — ECS Fargate cluster, task definitions per service, auto-scaling target-tracking policies | `feature/terraform-ecs` | AF-012 | 🟢 | ✅ |
| AF-014 | Asit | Supabase project setup — `supabase link`, RLS policies, pgvector extension, schema-per-tenant migrations (hosted; no RDS) | `feature/supabase-setup` | Phase 1 | 🟢 | ❌ |
| AF-015 | Asit | Terraform module `elasticache` — Redis 7 cluster (Multi-AZ), subnet groups, auth token | `feature/terraform-elasticache` | AF-012 | 🟢 | ❌ |
| AF-016 | Asit | Terraform module `s3` — artifacts bucket, RLHF data lake, prompt-templates bucket; S3 Object Lock on audit bucket (7 yr) | `feature/terraform-s3` | AF-012 | 🟢 | ❌ |
| AF-017 | Asit | Terraform module `messaging` — Confluent Kafka (primary bus + LLMOps telemetry), EventBridge bus + rules, per-pillar SQS queues + DLQs, SNS topic | `feature/terraform-messaging` | AF-012 | 🟢 | ❌ |
| AF-018 | Asit→Vishal | Terraform module `alb` — Application Load Balancer (L7), HTTPS listener, target groups per ECS service; CloudFront + WAF + Shield | `feature/terraform-alb` | AF-013 | 🟡 | ✅* |
| AF-019 | Asit→Vishal | Terraform module `iam` — least-privilege task execution roles per ECS service, no wildcard `*:*` policies | `feature/terraform-iam` | AF-012 | 🟢 | ✅ |
| AF-020 | Asit→Vishal | Terraform module `secrets` — Secrets Manager entries + SSM Parameter Store hierarchy; KMS CMK for encryption at rest | `feature/terraform-secrets` | AF-012 | 🟢 | ✅ |
| AF-021 | Asit→Vishal | Terraform module `ecr` — one ECR repo per service, image scanning on push, lifecycle policies | `feature/terraform-ecr` | Phase 1 | 🟢 | ✅ |
| AF-022 | Asit | GitHub Actions — `ci.yml` (lint, typecheck, unit, integration, security scans), `deploy-staging.yml`, `deploy-prod.yml` (canary ramp); ECR push + CodeDeploy blue/green | `feature/cicd-pipeline` | AF-021 | 🟡 | ❌ |
| AF-023 | Asit (← Purnima support) | OpenTelemetry baseline — OTel SDK in backend (FastAPI), structured JSON logs (`trace_id · organization_id · run_id · agent_id · model · env`), Fluent Bit → CloudWatch | `feature/observability-baseline` | AF-028 | 🟡 | ❌ |
| AF-024 | Asit (← Purnima support) | Prometheus + Grafana — metrics endpoint on all services, RED + USE dashboards, per-tenant cost panel; LangSmith project wired | `feature/metrics-dashboards` | AF-023 | 🟡 | ❌ |

_Phase 3a — Core API & Data Layer_

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-025 | Somesh | Alembic migrations — `platform` schema (tenants, model_registry, prompt_registry, tool_registry, audit_log) | `feature/db-migrations-platform` | AF-014 | 🟡 | ✅ |
| AF-026 | Somesh | Alembic migrations — per-tenant schema (runs, artifacts, gates, step_events, memory_episodes, cost_ledger) + orchestrator schema (checkpoints) | `feature/db-migrations-tenant` | AF-025 | 🟡 | ✅ |
| AF-027 | Somesh | **⭐ UDAL** — `backend/app/db/` client: `relational()`, `vector()`, `graph()`, `object()`; `contextvars` tenant propagation, cross-tenant guard (SEV-1 on breach), lineage audit emit | `feature/udal-core` | AF-026 | 🟡 | ✅ |
| AF-028 | Somesh | FastAPI app bootstrap — lifespan, DI, global exception handler (`{code, message, requestId}`), CORS | `feature/fastapi-app-setup` | AF-027 | 🟡 | ✅ |
| AF-029 | Somesh | Auth middleware — Supabase JWT validation (`SUPABASE_JWT_SECRET`), OPA policy sidecar, `OrgContext` via `contextvars`, mTLS service-to-service | `feature/auth-middleware` | AF-028 | 🟢 | ✅ |
| AF-030 | Somesh | **⭐ REST endpoints** — `POST /v1/ideas`, `GET /v1/runs/{id}`, `POST /v1/runs/{id}/gates/{gate_id}`, `GET /v1/runs/{id}/artifacts`, `POST /v1/feedback`, `GET /v1/llmops/cost`; OpenAPI 3.1 spec | `feature/rest-api-endpoints` | AF-028 | 🟢 | ✅ |
| AF-031 | Somesh | Supabase Realtime — subscribe to `step_events` changes (pg_notify); frontend uses `@supabase/supabase-js` channel; reconnect replay from `step_events` | `feature/realtime-integration` | AF-026 | 🟡 | ✅ |
| AF-032 | Somesh | Redis integration — session cache, LangGraph plan checkpoints, semantic prompt cache (`llm:prompt_cache:{sha256}`), embedding cache, per-tenant cost accumulator | `feature/redis-integration` | AF-015, AF-028 | 🟢 | ✅ |

_Phase 3b — LangGraph Orchestration_

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-033 | Somesh | **⭐ `RunState` TypedDict + `StateGraph` factory** — nodes per pillar step, conditional edges, checkpointing to Postgres + Redis after every node | `feature/langgraph-graph` | AF-027, AF-032 | 🟢 | ✅ |
| AF-034 | Somesh | HITL gate state machine — `pending → approved / rejected / timed_out`; EventBridge `gate.required` emit; SQS consumer for gate decisions | `feature/hitl-gate-manager` | AF-033, AF-017 | 🟢 | ✅ |
| AF-035 | Somesh | SQS worker loop — poll per-pillar queues, deserialise step, dispatch to agent runner, exponential backoff + jitter, DLQ escalation | `feature/sqs-worker` | AF-017, AF-033 | 🟢 | ✅ |

_Agent foundation + Tool Registry shell_

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-036 | Asit / ⚪ shared | **⭐ `BaseAgent` ABC** — `understand()`, `plan()`, `execute()`, `verify()`, `learn()`; typed error hierarchy; circuit breakers on LLM + tool calls. **Blocks ALL agents.** | `feature/base-agent` | AF-027 | 🔴 | ❌ |
| AF-047 | Asit (shell) + all pillars (entries) | Tool Registry + tools — `ToolRegistry` singleton; research tools (Tavily, SerpAPI, Crunchbase, G2); engineering tools (GitHub, Stripe, AWS Pricing API); marketing tools (X, LinkedIn, Resend, ProductHunt) | `feature/tool-registry` | AF-027 | 🟡 | ❌ |

**🟢 Do today (no blockers):** All of Phase 2 infra. Drive the **critical path** in this order:
`AF-012 networking → AF-013 ECS → AF-014 Supabase → AF-025/026 migrations → ~~AF-027 UDAL~~ ✅ → ~~AF-028 FastAPI~~ ✅ → ~~AF-030 REST contracts~~ ✅ → AF-036 BaseAgent`.
Those turn **7 pillar owners from 🟡 to 🟢**.

**🟢 Now unblocked (AF-028 ✅):** ~~AF-029 Auth middleware~~ ✅, ~~AF-030 REST endpoints~~ ✅.
**🟢 Now Complete:** Orchestrator AF-033–035, Redis AF-032.

**⚠️ You are a single point of failure** — you own infra **and** the BaseAgent (AF-036). The orchestrator (AF-033–035) and Redis (AF-032) have been successfully delegated to Somesh and completed.

---

## 2. Somesh Chitranshi — Pillar 1: Idea Validation & Market Research (also owns Orchestrator & Redis) 🟡

**Owns:** AF-025 → AF-035 (Alembic/UDAL/FastAPI/Redis/Orchestrator) · AF-037 Strategy · AF-038 Research · AF-039 Product Planner.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-032 | Somesh | Redis integration — session cache, LangGraph plan checkpoints, semantic prompt cache (`llm:prompt_cache:{sha256}`), embedding cache, per-tenant cost accumulator | `feature/redis-integration` | AF-015, AF-028 | 🟢 | ✅ |
| AF-033 | Somesh | **⭐ `RunState` TypedDict + `StateGraph` factory** — nodes per pillar step, conditional edges, checkpointing to Postgres + Redis after every node | `feature/langgraph-graph` | AF-027, AF-032 | 🟢 | ✅ |
| AF-034 | Somesh | HITL gate state machine — `pending → approved / rejected / timed_out`; EventBridge `gate.required` emit; SQS consumer for gate decisions | `feature/hitl-gate-manager` | AF-033, AF-017 | 🟢 | ✅ |
| AF-035 | Somesh | SQS worker loop — poll per-pillar queues, deserialise step, dispatch to agent runner, exponential backoff + jitter, DLQ escalation | `feature/sqs-worker` | AF-017, AF-033 | 🟢 | ✅ |
| AF-037 | Somesh | Strategy & Ideation Agent (Pillar 1) — TAM/SAM/SOM, competitor discovery, persona gen, Lean Canvas, viability 0–100, bias audit, 3 pivots; SLA < 30 min | `feature/strategy-agent` | AF-036, AF-048, AF-049 | 🟡 | ❌ |
| AF-038 | Somesh | Research Agent (Pillar 1) — Tavily + SerpAPI + Crunchbase + G2 + SimilarWeb fan-out, synthesis, citation groundedness check | `feature/research-agent` | AF-036, AF-047 | 🟡 | ❌ |
| AF-039 | Somesh | Product Planner Agent (Pillar 1.5) — PRD generation, roadmap, user stories, requirements extraction from strategy output | `feature/product-planner-agent` | AF-037 | 🟡 | ❌ |

**🟢 Do today (offline — no platform needed):**
- Jinja2 **prompt templates**: market sizing (TAM/SAM/SOM), competitor discovery, persona generation, Lean Canvas, viability scoring, bias audit, pivot suggestions, PRD generation.
- **Tool wrappers** as standalone modules: Tavily, SerpAPI, Crunchbase, G2, SimilarWeb.
- **Pydantic output schemas**: `{lean_canvas, viability_score, icps[], competitors[], sources[]}`, PRD schema.
- **Golden eval datasets** (Promptfoo) + **mocked unit tests** (fake LLM + fake UDAL).

**🔴 Blocked on:** AF-036 BaseAgent, AF-048 Prompt Registry, AF-049 LLM Router (to wire all 3 agents).
**⚠️ Load:** 3 of the team's 9 agents — flag to Asit whether Research or Product Planner should move to a lighter owner.

---

## 3. Kaushlendra Kumar Gupta — Pillar 2: Architecture & Tech Stack 🟡

**Owns:** AF-040 Architect Agent.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-040 | Kaushlendra | Architect Agent (Pillar 2) — FR/NFR extraction, ERD, OpenAPI contract, stack selection, microservice boundaries, cost forecast; HITL approval gate | `feature/architect-agent` | AF-036, AF-039 | 🟡 | ❌ |

**🟢 Do today (offline):** Architect prompt templates (FR/NFR extraction, stack selection, microservice boundaries, cost forecast); ERD generation logic (Mermaid); OpenAPI 3.1 contract generator; AWS Pricing API tool wrapper; output schemas; golden evals; mocked tests.

**🔴 Blocked on:** AF-036 + foundation. **🔗 Soft dependency:** consumes **Pillar 1's** Lean Canvas + personas (AF-037/039) — **agree the schema with Somesh now** so contracts line up.

---

## 4. Kartik Mogalapalli — Pillar 3: Autonomous Code Generation 🟡

**Owns:** AF-041 Coder Agent.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-041 | Kartik | Coder Agent (Pillar 3) — Frontend Specialist (Next.js 14 + Tailwind + shadcn/ui) ∥ Backend Specialist (FastAPI + SQLAlchemy + Supabase Auth + Stripe); Alembic migrations; zero lint errors; CI/CD scaffold | `feature/coder-agent` | AF-036, AF-040 | 🟡 | ❌ |

**🟢 Do today (offline):** Code-gen prompt templates (Next.js 14 + Tailwind + shadcn/ui; FastAPI + SQLAlchemy + Supabase Auth + Stripe); repo-scaffolding templates; GitHub + Stripe tool wrappers; output schemas; golden evals (compile-clean, lint-clean); mocked tests.

**🔴 Blocked on:** AF-036 + foundation. **🔗 Soft dependency:** consumes **Pillar 2's** ERD + OpenAPI (AF-040) — coordinate schema with Kaushlendra now.

---

## 5. Vishal Prasad — Pillar 4: Testing & Self-Healing 🟡

**Owns:** AF-042 Reviewer / Self-Healer Agent.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-042 | Vishal | Reviewer / Self-Healer Agent (Pillar 4) — static analysis, unit + integration test gen, security scans (Trivy/Semgrep/Snyk), sandbox execution, AST-aware patching, LLM-as-judge; max 5 cycles; coverage ≥ 80% | `feature/reviewer-agent` | AF-036, AF-041 | 🟡 | ❌ |

**🟢 Do today (lots of standalone work here):**
- **Sandbox runner** prototype: ephemeral Docker + isolated network + Testcontainers — largely self-contained; test it on any sample repo today.
- **Security-scan wrappers**: Trivy, Semgrep, Snyk, Gitleaks as standalone modules with typed outputs.
- Prompt templates: unit/integration test generation, AST-aware patching, LLM-as-judge review.
- Self-heal loop (max 5 cycles) as a pure state machine; output schema `{coverage, scan_results[], patches[], verdict}`; golden evals; mocked tests.

**🔴 Blocked on:** AF-036 + foundation. **🔗 Soft dependency:** needs **Pillar 3's** generated code (AF-041) to test — but validate your whole pipeline against any sample Next.js/FastAPI repo in the meantime.

---

## 6. Prasenjit Roy — Pillar 5: Deployment & Infrastructure 🟡

**Owns:** AF-043 DevOps Agent.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-043 | Prasenjit | DevOps Agent (Pillar 5) — multi-stage Dockerfile, Terraform plan + apply, ECS provisioning, Route 53 + ACM, monitoring setup, smoke test; SLA < 10 min; infra-spend HITL gate | `feature/devops-agent` | AF-036, AF-042 | 🟡 | ❌ |

**🟢 Do today (offline):** Multi-stage Dockerfile templates; Terraform plan/apply generation templates; ECS provisioning logic; Route 53 + ACM (DNS/SSL) flow; smoke-test runner; prompt templates; output schemas; golden evals; mocked tests.
**🤝 Pair with Asit:** the Terraform you write for the *product* mirrors the Terraform Asit writes for the *platform* (AF-012–021) — share modules.

**🔴 Blocked on:** AF-036 + foundation. **🔗 Soft dependency:** needs **Pillar 3/4** output (a tested repo) to deploy.

---

## 7. Pallavi Anil Sindkar — Pillar 6: Marketing & Launch Automation 🟡

**Owns:** AF-044 Marketing Agent.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-044 | Pallavi | Marketing Agent (Pillar 6) — brand kit (DALL-E 3), landing page, SEO engine (10 blog drafts), email drip sequences, social posts; feature-list hallucination cross-ref; Launch Control Center HITL gate | `feature/marketing-agent` | AF-036, AF-040 | 🟡 | ❌ |

**🟢 Do today (offline):** Prompt templates (brand kit, landing page, 10-blog SEO engine, email drip sequences, Product Hunt kit, X thread, HN post); DALL-E 3 + Resend + X/LinkedIn/ProductHunt tool wrappers; the **feature-claim cross-reference check** (anti-hallucination) as a standalone validator; output schemas; golden evals; mocked tests.

**🔴 Blocked on:** AF-036 + foundation. **🔗 Soft dependency:** the hallucination check needs **Pillar 2's** feature list (AF-040) — coordinate with Kaushlendra.

---

## 8. Purnima — Pillar 7: LLMOps & Continuous Learning 🟡 (also owns shared 3d)

**Owns (4 tasks):** AF-045 LLMOps Agent **+ shared platform** AF-048 Prompt Registry, AF-049 LiteLLM Router + RAG, AF-050 Eval harness. *(These three partially unblock everyone — prioritise them.)*

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-048 | Purnima (shell) + all pillars (prompts) | Prompt Registry — versioned Jinja2 templates in `prompt_registry` table + S3; `get()` resolves active/canary; deterministic canary split; strict variable validation | `feature/prompt-registry` | AF-025 | 🟡 | ❌ |
| AF-049 | Purnima | LiteLLM Model Router + RAG — task-class → model routing (Gemini 3.5 Flash; gemini-embedding-2 768-dim); hybrid BM25 + ANN on Supabase pgvector; Cohere reranking; context compression; citation check | `feature/model-router-rag` | AF-027, AF-014 | 🟡 | ❌ |
| AF-050 | Purnima + pillar golden sets | Eval harness — Promptfoo golden sets per agent, LangSmith batch eval runner, CI gate blocking prompt promotion on score regression > 2% | `feature/eval-harness` | AF-048 | 🟡 | ❌ |
| AF-045 | Purnima | LLMOps Agent (Pillar 7) — trace analysis, DSPy prompt optimisation, Promptfoo regression, LiteLLM routing updates, TruLens drift monitoring, A/B experiments, FinOps report; weekly Step Functions cycle | `feature/llmops-agent` | AF-036, all agents running | 🔴 | ❌ |

**🟢 Do today (high leverage — on everyone's critical path):**
- **AF-050 Eval harness** + Promptfoo golden-set runner scaffold (pillar owners plug their sets in).
- **AF-049 LiteLLM Router rules** (task-class → Gemini 3.5 Flash) + RAG pipeline (hybrid BM25 + ANN, reranking, citation check) against test data.
- **AF-048 Prompt Registry** loader + versioning logic.
- Drift monitoring (TruLens/Evidently) + FinOps report logic.

**🔴 Blocked on (the LLMOps *agent* itself, AF-045):** needs agents actually running to analyse live traces / run A/B — so AF-045 is **last**. Build the shared registry/router/eval **first**.

---

## 9. Raunak Ravi — Web Interface Design 🟢 START NOW (design)

**Owns (12 tasks):** AF-051 → AF-062.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-051 | Raunak | Next.js 14 App Router — TypeScript strict, Tailwind, shadcn/ui, Supabase Auth (`@supabase/supabase-js` + `@supabase/ssr`), global error boundary + Sentry | `feature/nextjs-setup` | Phase 1 | 🟢 | ❌ |
| AF-052 | Raunak | Typed API client (`lib/api-client.ts`) + Realtime hook (`lib/realtime-client.ts`) — `useRun()` merging React Query + Supabase Realtime, `useGate()` polling + mutation | `feature/api-client-hooks` | AF-030, AF-031 | 🔴 | ❌ |
| AF-053 | Raunak | Zustand stores + React Query config — `runStore`, `gateStore`, `uiStore`; responsive layout shell with live cost ticker | `feature/state-management` | AF-051 | 🟢 | ❌ |
| AF-054 | Raunak | Idea Intake surface — multi-modal form (text, PDF, voice, URL), locale selector, `POST /v1/ideas`, redirect to run page | `feature/idea-intake-ui` | AF-052 (real) | 🟡 | ❌ |
| AF-055 | Raunak | Validation Studio (Pillar 1) — Lean Canvas viewer, viability gauge 0–100, ICP cards, pivot picker, approve/pivot HITL UI | `feature/validation-studio` | AF-037 (data) | 🟡 | ❌ |
| AF-056 | Raunak | Architecture Studio (Pillar 2) — Mermaid ERD renderer, Swagger UI OpenAPI viewer, stack card, cost forecast, approve/reject HITL UI | `feature/architecture-studio` | AF-040 (data) | 🟡 | ❌ |
| AF-057 | Raunak | Code Review Studio (Pillar 3–4) — Monaco diff viewer, Reviewer comments panel, self-heal cycle progress, security scan results table | `feature/code-review-studio` | AF-042 (data) | 🟡 | ❌ |
| AF-058 | Raunak | Deploy Console (Pillar 5) — live deployment log stream, infra-spend HITL gate, smoke test card, live URL badge, 1-click rollback | `feature/deploy-console` | AF-043 (data) | 🟡 | ❌ |
| AF-059 | Raunak | Launch Control Center (Pillar 6) — brand kit preview, landing page iframe, social post drafts edit-in-place, email sequence preview, approve/edit HITL; nothing publishes without founder sign-off | `feature/launch-control-center` | AF-044 (data) | 🟡 | ❌ |
| AF-060 | Raunak | LLMOps Dashboard (Pillar 7) — cost by model/pillar/run, drift score time-series, eval score history, prompt version table with canary indicator | `feature/llmops-dashboard` | AF-045 (data) | 🟡 | ❌ |
| AF-061 | Raunak | Run List / Dashboard — all runs with status, pillar, cost, created date; filter + search; skeleton loaders | `feature/run-dashboard` | AF-030 | 🟡 | ❌ |
| AF-062 | Raunak | Admin Dashboard — tenant CRUD, model registry mgmt, prompt registry lifecycle, tool registry, audit log viewer, platform FinOps view ⚠️ *(large — flag if too much)* | `feature/admin-dashboard` | AF-030 | 🟡 | ❌ |

**🟢 Do today (no backend needed):**
- AF-051 Next.js 14 + Tailwind + shadcn/ui setup · AF-053 Zustand + React Query scaffolding.
- **All pillar surfaces as static screens with mock data:** Idea Intake, Validation Studio, Architecture Studio, Code Review Studio, Deploy Console, Launch Control Center, LLMOps Dashboard, Run Dashboard, Admin.
- Full design system / component library.

**🔴 Blocked on:** AF-052 (typed API client + Realtime hook) needs **AF-030 REST contracts** + **AF-031 Realtime**. **Plan:** build every screen on mock data now → swap in the real API client when Phase 3 lands.
**⚠️ Load:** AF-062 Admin Dashboard is large — flag if 12 surfaces is too much for one person.

---

## 10. Yogesh Raut — Mobile Interface Design 🟢 START NOW (design)

**Owns (9 tasks):** AF-063 → AF-071.

| ID | Owner | Task | Branch | Depends on | Start | Status |
|----|-------|------|--------|------------|:----:|:----:|
| AF-063 | Yogesh | Expo Router scaffold — TS strict, Supabase Auth (`@supabase/supabase-js` + `ExpoSecureStoreAdapter`), secure token storage in `expo-secure-store`, shared API client from `packages/api-client` | `feature/expo-setup` | Phase 1 | 🟢 | ❌ |
| AF-064 | Yogesh | Push notifications — Expo Push → SNS → realtime; deep-link on tap to gate or run screen | `feature/push-notifications` | AF-017 (SNS) | 🔴 | ❌ |
| AF-065 | Yogesh | Idea Intake screen — text input, voice record (Expo AV), file attach; submit to `POST /v1/ideas` | `feature/mobile-idea-intake` | AF-030 | 🟡 | ❌ |
| AF-066 | Yogesh | Run Dashboard screen — live run list with status badges + cost; pull-to-refresh; realtime updates | `feature/mobile-run-dashboard` | AF-030, AF-031 | 🟡 | ❌ |
| AF-067 | Yogesh | Run Detail screen — current pillar progress, step log stream, active gate banner | `feature/mobile-run-detail` | AF-031 | 🟡 | ❌ |
| AF-068 | Yogesh | HITL Gate Approval screens — gate-specific review UI (Lean Canvas, Architecture summary, Launch preview); approve/reject with note; offline queue + sync on reconnect | `feature/mobile-gate-approval` | AF-034 | 🟡 | ❌ |
| AF-069 | Yogesh | Artifacts Viewer — browse outputs (canvas, ERD image, live URL, brand kit, social posts) | `feature/mobile-artifacts-viewer` | AF-030 | 🟡 | ❌ |
| AF-070 | Yogesh | LLMOps Summary screen — cost card, eval score card, last drift check; dark/light mode following system | `feature/mobile-llmops-summary` | AF-045 (data) | 🟡 | ❌ |
| AF-071 | Yogesh | EAS Build + release — `eas.json` profiles (development, preview, production); App Store + Google Play submit via `eas submit` | `feature/eas-build-pipeline` | AF-063 | 🟢 | ❌ |

**🟢 Do today (no backend needed):** Expo Router scaffold (AF-063), navigation, secure-storage auth flow, all screens with mock data, design system, dark/light mode, EAS build profiles (AF-071).

**🔴 Blocked on:** real-API screens + AF-064 push notifications need **Phase 3** + AF-031 Realtime + AF-017 SNS. Build on mock data now.

---

# PART C — Dependency Graph & How to Connect

## Phase dependency chain

```
Phase 1 ✅ DONE
   │
   ▼
ASIT ──► Phase 2 Infra (AF-012–024)
   │        └─ enables ──► Phase 3a Foundation (AF-025–032: UDAL, FastAPI, Auth, Redis, Realtime)
   │                            └─ + Phase 3b Orchestrator (AF-033–035) + BaseAgent (AF-036)
   │                                     │
   │     ┌───────────── PURNIMA shared 3d (AF-048 Prompt Reg / AF-049 Router+RAG / AF-050 Eval) ─────────────┐
   │     ▼                                                                                                    ▼
   │  ALL 7 PILLAR OWNERS WIRE their agents (AF-037–045)
   │  Somesh(P1) ─► Kaushlendra(P2) ─► Kartik(P3) ─► Vishal(P4) ─► Prasenjit(P5)   [each consumes the previous pillar's output]
   │  Pallavi(P6) needs P2 feature list · Purnima(P7 agent) needs all agents running (last)
   │
   ▼  (independent track — starts immediately, integrates after Phase 3 contracts are stable)
RAUNAK (Web)  +  YOGESH (Mobile)  +  ASIT (VS Code Extension, AF-072–078)
```

## The wiring order — how each piece "connects" (do this, in this order)

1. **Somesh publishes the data contracts first.** Before the platform is even finished, Somesh commits the **Pydantic I/O schemas** for each pillar (agent input/output) + the **OpenAPI 3.1 spec** (AF-030). This lets everyone build against a *frozen contract* instead of waiting.
2. **Somesh/Asit land the foundation:** ~~AF-027 UDAL~~ ✅ → ~~AF-028 FastAPI~~ ✅ → AF-036 BaseAgent. ← this is the moment 🟡 → 🟢 for all agent owners.
3. **Purnima lands the agent plumbing:** AF-048 Prompt Registry + AF-049 LLM Router. Agent owners' offline prompts/tools now plug into real infrastructure.
4. **Each pillar owner wires their agent** by subclassing `BaseAgent`, registering tools in the Tool Registry (AF-047), and reading/writing through UDAL. They drop in the prompts + schemas + tools they already built offline.
5. **Agent-to-agent connection** = the Orchestrator (AF-033). The LangGraph `StateGraph` calls Pillar 1 → 2 → 3 … in order, passing each agent's output as the next agent's input (via `RunState`). This is why pillar output schemas must be agreed early (see soft deps).
6. **Frontend/Mobile connect last:** Raunak swaps mock data for the typed API client (AF-052) once AF-030 + AF-031 are live; Yogesh does the same on mobile.
7. **LLMOps closes the loop:** once agents run, Purnima's AF-045 reads traces (LangSmith) and feeds prompt/model improvements back in.

## Soft (agent-to-agent) dependencies — agree these schemas NOW

| Producer | Output (agree the schema) | Consumer |
|----------|---------------------------|----------|
| Somesh — Pillar 1 (AF-037/039) | Lean Canvas + personas + PRD | Kaushlendra — Pillar 2 |
| Kaushlendra — Pillar 2 (AF-040) | ERD + OpenAPI + **feature list** | Kartik — Pillar 3 **and** Pallavi — Pillar 6 |
| Kartik — Pillar 3 (AF-041) | Generated repo | Vishal — Pillar 4 |
| Vishal — Pillar 4 (AF-042) | Tested, green repo | Prasenjit — Pillar 5 |
| Prasenjit — Pillar 5 (AF-043) | Live URL + deploy status | Raunak/Yogesh UIs |
| All agents | Run traces / events | Purnima — Pillar 7 |

---

# PART D — What's Missing (Gaps & Unassigned)

These are real parts of the plan/architecture with **no clear owner**. Asit to assign.

| # | Gap | Tasks / Area | Why it matters | Suggested fix |
|---|-----|--------------|----------------|---------------|
| **A** | ✅ **VS Code Extension — assigned to Asit** | AF-072 → AF-078 (entire Phase 6) | A whole product surface (in-IDE co-founder) | **RESOLVED 2026-06-04 → Asit.** Plan: `developer-plans/12-asit-vscode-extension-plan.md`. Delegate to Raunak (TS/UI overlap) if Asit overloaded. |
| **B** | ✅ **Foundation overloaded on Lead — Resolved** | BaseAgent AF-036 | BaseAgent ABC wraps every agent call | **RESOLVED 2026-06-06:** Orchestrator (AF-033–035) and Redis (AF-032) delegated to Somesh and completed. Asit still owns BaseAgent AF-036. |
| **C** | ✅ **Guardrails pipeline — assigned to Asit** | AF-046 (OPA, Presidio, Llama Guard, TruLens, Evidently) | Wraps **every** agent call; security/compliance backbone | **RESOLVED 2026-06-04 → Asit** (Purnima co-owns output/monitoring stages). Plan: `developer-plans/11-asit-guardrails-pipeline-plan.md`. |
| **D** | ⚪ **Pillar 1 overloaded** | Somesh owns AF-037 + AF-038 + AF-039 (3 agents) | Slowest pillar slows the whole chain (P2→P3… wait on P1) | Reassign Research **or** Product Planner to a lighter owner |
| **E** | ✅ **Finance & Ops/Risk agents — owner recorded: Asit** | Canonical roster (CLAUDE.md §7.1); not in Phase 1 list | Needed in Phase 4; cross-cutting | **RESOLVED 2026-06-04 → Asit (Phase 4, design deferred).** Plan: `developer-plans/13-asit-finance-ops-risk-plan.md`. |
| **F** | ⚪ **Registry shells — split ownership** | AF-047 Tool Registry, AF-048 Prompt Registry | Each pillar adds entries, but the *shell* needs one owner | Tool Registry → Asit; Prompt Registry → Purnima; pillars contribute entries |
| **G** | ⚪ **Team's own QA / integration tests** | (not a single AF-ID) | The Reviewer **agent** (Vishal) tests *generated* apps — different from testing *our* platform | Lead owns platform CI gates (AF-022); each owner writes own unit tests |
| **H** | ⚪ **Graph DB (Neo4j) + Feature Store (Feast)** | Architecture Layer 5 / Layer 10 | In blueprint, no owner, deferred | Defer to Phase 4; note owner = Purnima-adjacent |
| **I** | ⚪ **Observability content owner** | AF-023/024 dashboards | Asit builds the infra; *who designs the dashboards/alerts?* | Asit (infra) + Purnima (LLMOps metrics) co-own |

---

# PART E — Recommendations (for the Lead)

1. **Unblock first, in this order:** ~~AF-027 UDAL~~ ✅ → AF-036 BaseAgent → ~~AF-028 FastAPI~~ ✅ → ~~AF-030 REST contracts~~ ✅. These four flip 7 people from 🟡 to 🟢. (AF-027 + AF-028 + AF-030 done — next: AF-036.)
2. **Publish agent I/O contracts (Pydantic schemas) on day 1** so pillar owners build against a fixed contract while the platform is still being wired.
3. **Gaps A / C / E assigned to Asit** (VS Code Extension, Guardrails, Finance & Ops/Risk) as of 2026-06-04. Still open: **B** (delegate foundation — now more urgent at 34 tasks), **D** (rebalance Pillar 1), and ownership notes F/G/H/I.
4. **Rebalance Pillar 1 (D)** — move one of Somesh's 3 agents.
5. **Tell everyone to start their 🟡 offline work now** — prompts, tools, schemas, evals, mocked tests, UI mockups. Idle-waiting on the foundation is the biggest avoidable cost.

---

## Changelog

| Date | Version | Description |
|------|---------|-------------|
| 2026-06-06 | 3.2.0 | AF-032 to AF-035 marked ✅ and assigned to Somesh. Redis integration, RunState TypedDict + StateGraph factory, HITL gate state machine, and SQS worker loop are now complete. Overload on Lead reduced. |
| 2026-06-04 | 3.1.0 | AF-027 UDAL marked ✅ (Somesh). Implemented: context.py, audit.py, relational.py, vector.py, graph.py, object_store.py, udal.py rewrite, get_udal() dep, supabase settings. 14 unit tests, ruff+mypy clean. Phase 3 done: 2→3, pending: 24→23. Total done: 13→14. |
| 2026-06-04 | 3.0.0 | Assigned all previously-unassigned work to **Asit**: AF-046 (Guardrails), AF-072→AF-078 (VS Code Extension), Finance & Ops/Risk agents (Phase 4). Updated roster, status overview, per-person counts (Asit 26→34, Unassigned 8→0), Part A (3d + Phase 6 owners), Part B, Part D gaps A/C/E (resolved), Part E. Added `developer-plans/11–13`. Flagged Asit overload (bus-factor 1) + delegation recommendation. |
| 2026-06-01 | 2.0.0 | Rebuilt as single source of truth — full 78-task descriptions merged from `TASKS.md` (Part A by phase + Part B by person), with Owner / Depends-on / Start columns, wiring/connection guide (Part C), gaps (Part D), recommendations (Part E). No longer need `TASKS.md` to work. |
| 2026-06-01 | 1.0.0 | Initial per-person assignment + independence analysis + gap list |
```
