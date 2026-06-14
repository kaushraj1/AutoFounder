# AutoFounder AI — Task Tracker

> **AutoFounder AI** is a multi-tenant agentic AI SaaS platform that converts a single text idea into a fully validated, designed, built, tested, deployed, and marketed software business — autonomously, in days instead of months.

---

## Status Overview

| Phase | Description | Total | ✅ Done | ❌ Pending |
|-------|-------------|-------|---------|-----------|
| Phase 1 | Monorepo & Boilerplate Setup | 11 | 11 | 0 |
| Phase 2 | Infrastructure & Cloud | 13 | 13 | 0 |
| Phase 3 | Backend — FastAPI + Agents | 26 | 26 | 0 |
| Phase 4 | Frontend — Next.js 14 | 12 | 12 | 0 |
| Phase 5 | Mobile — Expo React Native | 9 | 9 | 0 |
| Phase 6 | VS Code Extension | 7 | 7 | 0 |
| **Total** | | **78** | **78** | **0** |

> Phase 2: **13/13 merged to `dev`** (PR #13). Phase 3: **18/26** done — AF-025–039 (foundation + orchestrator + BaseAgent + Pillar-1 agents) + AF-042 Reviewer + **AF-046 Guardrails + AF-047 Tool Registry** (`feat/platform/guardrails-tool-registry`); AF-040/041/043/044/045/048/049/050 pending. **Phase 6: 7/7** done (`feature/vscode-extension`) — full TypeScript VS Code extension (esbuild-bundled, `tsc`+ESLint+Prettier clean, 35 unit tests, `vsce package` verified); built against the AF-030/031/034 contract with graceful fallbacks where AF-031 Realtime / AF-041 Coder are still landing. Documented Phase-2 follow-ups: AF-017 (Confluent), AF-018 (CloudFront/Shield), AF-022 (blue/green canary), AF-023 (FireLens sidecar), AF-024 (deployed Prometheus/Grafana + live LangSmith) — see footnotes.

---

## Phase 1 — Monorepo & Boilerplate Setup

> Foundation: workspace tooling, Docker, linting, scripts, and per-component scaffolds.
> **All tasks completed.**

| ID | Task | Branch | Status |
|----|------|--------|--------|
| AF-001 | Init pnpm workspace (`pnpm-workspace.yaml`) + Turborepo (`turbo.json`) with `dev`, `lint`, `build` pipelines | `feature/monorepo-init` | ✅ Completed |
| AF-002 | Root `package.json` — `turbo dev`, unified `lint`, `format:check` scripts wiring Ruff + ESLint | `feature/root-scripts` | ✅ Completed |
| AF-003 | `docker-compose.yml` — Redis 7 only (AOF persistence) with named volumes; Supabase CLI manages PostgreSQL + pgvector + Auth + Storage + Realtime locally via `supabase start` | `feature/docker-compose-setup` | ✅ Completed |
| AF-004 | Backend scaffold — `backend/` with `pyproject.toml`, `uv.lock`, Ruff + mypy + pytest config, `app/` layout, Alembic, `Dockerfile` | `feature/backend-scaffold` | ✅ Completed |
| AF-005 | Frontend scaffold — `frontend/` TypeScript + React placeholder, `tsconfig.json`, `package.json` | `feature/frontend-scaffold` | ✅ Completed |
| AF-006 | Mobile scaffold — `mobile-app/` Expo + TypeScript placeholder, `tsconfig.json`, `package.json` | `feature/mobile-scaffold` | ✅ Completed |
| AF-007 | VS Code Extension scaffold — `vscode-extension/` TypeScript placeholder, `tsconfig.json`, `package.json` | `feature/vscode-extension-scaffold` | ✅ Completed |
| AF-008 | ESLint v9 flat config (`eslint.config.mjs`) + Prettier — shared rules across all JS/TS workspaces | `feature/lint-config` | ✅ Completed |
| AF-009 | `Makefile` — `install`, `stack`, `stack-down`, `dev`, `backend-lint`, `js-lint`, `quality` targets | `feature/makefile-scripts` | ✅ Completed |
| AF-010 | `scripts/setup-dev.sh` + `scripts/setup-dev.ps1` — cross-platform one-command local environment setup | `feature/dev-setup-scripts` | ✅ Completed |
| AF-011 | `.env.example` + `README.md` — environment variable documentation and project onboarding guide | `feature/env-and-readme` | ✅ Completed |

---

## Phase 2 — Infrastructure & Cloud

> AWS networking, ECS services, managed databases, messaging, CI/CD pipeline, and observability baseline.
> **Depends on: Phase 1**

| ID | Task | Branch | Status |
|----|------|--------|--------|
| AF-012 | Terraform module `networking` — VPC, public/private subnets (Multi-AZ), NAT gateways, VPC endpoints for S3/ECR/Secrets | `feature/terraform-networking` | ✅ Completed |
| AF-013 | Terraform module `ecs` — ECS Fargate cluster, task definitions per service, auto-scaling target-tracking policies | `feature/terraform-ecs` | ✅ Completed |
| AF-014 | Supabase project setup — link Supabase project (`supabase link`), configure RLS policies, pgvector extension, schema-per-tenant migrations; Supabase is hosted (no RDS provisioning required) | `feature/supabase-setup` | ✅ Completed |
| AF-015 | Terraform module `elasticache` — Redis 7 cluster (Multi-AZ), subnet groups, auth token | `feature/terraform-elasticache` | ✅ Completed |
| AF-016 | Terraform module `s3` — artifacts bucket, RLHF data lake, prompt-templates bucket; S3 Object Lock on audit bucket (7 yr) | `feature/terraform-s3` | ✅ Completed |
| AF-017 | Terraform module `messaging` — Confluent Kafka cluster (primary inter-agent bus + LLMOps telemetry), EventBridge custom bus + rules, per-pillar SQS queues + DLQs, SNS notification topic | `feature/terraform-messaging` | ✅ Completed² |
| AF-018 | Terraform module `alb` — Application Load Balancer (L7), HTTPS listener, target groups per ECS service; CloudFront + WAF + Shield | `feature/terraform-alb` | ✅ Completed¹ |
| AF-019 | Terraform module `iam` — least-privilege task execution roles per ECS service, no wildcard `*:*` policies | `feature/terraform-iam` | ✅ Completed |
| AF-020 | Terraform module `secrets` — Secrets Manager entries + SSM Parameter Store hierarchy; KMS CMK for encryption at rest | `feature/terraform-secrets` | ✅ Completed |
| AF-021 | Terraform module `ecr` — one ECR repository per service, image scanning on push, lifecycle policies | `feature/terraform-ecr` | ✅ Completed |
| AF-022 | GitHub Actions workflows — `ci.yml` (lint, typecheck, unit, integration, security scans), `deploy-staging.yml`, `deploy-prod.yml` with canary ramp; ECR push + CodeDeploy blue/green | `feature/cicd-pipeline` | ✅ Completed³ |
| AF-023 | OpenTelemetry baseline — OTel SDK wired into backend (FastAPI), structured JSON logs with mandatory `trace_id · organization_id · run_id · agent_id · model · env` fields, Fluent Bit → CloudWatch | `feature/observability-baseline` | ✅ Completed⁴ |
| AF-024 | Prometheus + Grafana — metrics endpoint on all services, RED + USE dashboards, per-tenant cost attribution panel; LangSmith project created and wired | `feature/metrics-dashboards` | ✅ Completed⁵ |

> ¹ AF-018 ships ALB + HTTPS/HTTP listeners + per-service target groups + WAFv2 (AWS managed rules). CloudFront + Shield Advanced are a documented follow-up (CloudFront needs a us-east-1 ACM cert; Shield Advanced is a paid add-on).
> ² AF-017 ships the AWS-native bus (EventBridge + per-pillar SQS/DLQs + gate-decisions queue + SNS) the orchestrator uses. Confluent Kafka is deferred (separate provider + Confluent Cloud account).
> ³ AF-022: CI + functional **rolling** CD (deploy workflows reconciled to the real `autofounder-ai-*` resources, circuit-breaker auto-rollback) done. CodeDeploy **blue/green canary** is documented (`infra/codedeploy/README.md` + appspec/taskdef), not yet coded — needs an AWS apply-test. CD auth → GitHub OIDC is a follow-up.
> ⁴ AF-023: OTel SDK (gated) + mandatory JSON log fields (env/trace_id auto; org/run/agent/model via contextvars) + Fluent Bit config done. Wiring the FireLens sidecar into the ECS task def is a follow-up (awslogs already ships logs to CloudWatch).
> ⁵ AF-024: `/metrics` + metric vocabulary + Prometheus scrape config + Grafana RED/cost dashboard done. Deploying the Prometheus/Grafana stack + live LangSmith tracing are follow-ups.

---

## Phase 3 — Backend (FastAPI + LangGraph + Agents)

> Core API, orchestration engine, all AI agents, guardrails, tool registry, prompt registry, and RAG pipeline.
> **Depends on: Phase 2**

### 3a — Core API & Data Layer

| ID | Task | Branch | Status |
|----|------|--------|--------|
| AF-025 | Alembic migrations — `platform` schema (tenants, model_registry, prompt_registry, tool_registry, audit_log) | `feature/db-migrations-platform` | ✅ Completed |
| AF-026 | Alembic migrations — per-tenant schema (runs, artifacts, gates, step_events, memory_episodes, cost_ledger) and orchestrator schema (checkpoints) | `feature/db-migrations-tenant` | ✅ Completed |
| AF-027 | UDAL — `backend/app/db/` Python client: `relational()`, `vector()`, `graph()`, `object()`; `contextvars` tenant propagation, cross-tenant guard (SEV-1 on breach), lineage audit emit | `feature/udal-core` | ✅ Completed |
| AF-028 | FastAPI app bootstrap — lifespan, dependency injection, global exception handler (structured `{code, message, requestId}` response), CORS | `feature/fastapi-app-setup` | ✅ Completed |
| AF-029 | Auth middleware — Supabase JWT validation (SUPABASE_JWT_SECRET), OPA policy sidecar integration, `OrgContext` via `contextvars`, mTLS service-to-service | `feature/auth-middleware` | ✅ Completed |
| AF-030 | REST API endpoints — `POST /v1/ideas`, `GET /v1/runs/{id}`, `POST /v1/runs/{id}/gates/{gate_id}`, `GET /v1/runs/{id}/artifacts`, `POST /v1/feedback`, `GET /v1/llmops/cost`; OpenAPI 3.1 spec | `feature/rest-api-endpoints` | ✅ Completed |
| AF-031 | Supabase Realtime integration — subscribe to `step_events` table changes via Supabase Realtime (pg_notify); frontend uses `@supabase/supabase-js` Realtime channel; reconnect replay from `step_events` | `feature/realtime-integration` | ✅ Completed |
| AF-032 | Redis integration — session cache, LangGraph plan checkpoints, semantic prompt cache (`llm:prompt_cache:{sha256}`), embedding cache, per-tenant cost accumulator | `feature/redis-integration` | ✅ Completed |

### 3b — LangGraph Orchestration

| ID | Task | Branch | Status |
|----|------|--------|--------|
| AF-033 | `RunState` TypedDict + `StateGraph` factory — nodes for every pillar step, conditional edges, checkpointing to Postgres + Redis after every node | `feature/langgraph-graph` | ✅ Completed |
| AF-034 | HITL gate state machine — `pending → approved / rejected / timed_out`; EventBridge `gate.required` emit; SQS consumer for gate decisions from API | `feature/hitl-gate-manager` | ✅ Completed |
| AF-035 | SQS worker loop — poll per-pillar queues, deserialise step, dispatch to agent runner, exponential backoff + jitter, DLQ escalation | `feature/sqs-worker` | ✅ Completed |

### 3c — AI Agents

| ID | Task | Branch | Status |
|----|------|--------|--------|
| AF-036 | `BaseAgent` ABC — `understand()`, `plan()`, `execute()`, `verify()`, `learn()`; typed error hierarchy; circuit breakers on LLM + tool calls | `feature/base-agent` | ✅ Completed |
| AF-037 | Strategy & Ideation Agent (Pillar 1) — TAM/SAM/SOM, competitor discovery, persona gen, Lean Canvas, viability score 0–100, bias audit, 3 pivot options; SLA < 30 min | `feature/strategy-agent` | ✅ Completed |
| AF-038 | Research Agent (Pillar 1) — Tavily + SerpAPI + Crunchbase + G2 + SimilarWeb tool fan-out, synthesis, citation groundedness check | `feature/research-agent` | ✅ Completed |
| AF-039 | Product Planner Agent (Pillar 1.5) — PRD generation, roadmap, user stories, requirements extraction from strategy output | `feature/product-planner-agent` | ✅ Completed |

| AF-041 | Coder Agent (Pillar 3) — Frontend Specialist (Next.js 14 + Tailwind + shadcn/ui) ∥ Backend Specialist (FastAPI + SQLAlchemy + Supabase Auth + Stripe); Alembic DB migrations; zero lint errors; CI/CD scaffold | `feature/coder-agent` | ❌ Pending |
| AF-042 | Reviewer / Self-Healer Agent (Pillar 4) — static analysis, unit + integration test gen, security scans (Trivy/Semgrep/Snyk), sandbox execution, AST-aware patching, LLM-as-judge; max 5 cycles; coverage ≥ 80% | `feature/reviewer-agent` | ✅ Completed |
| AF-043 | DevOps Agent (Pillar 5) — multi-stage Dockerfile, Terraform plan + apply, ECS provisioning, Route 53 + ACM, monitoring setup, smoke test; SLA < 10 min; infra-spend HITL gate | `feature/devops-agent` | ❌ Pending |
| AF-044 | Marketing Agent (Pillar 6) — brand kit (DALL-E 3), landing page, SEO content engine (10 blog drafts), email drip sequences, social posts; feature-list hallucination cross-ref; Launch Control Center HITL gate | `feature/marketing-agent` | ❌ Pending |
| AF-045 | LLMOps Agent (Pillar 7) — trace analysis, DSPy prompt optimisation, Promptfoo regression, LiteLLM routing updates, TruLens drift monitoring, A/B experiments, FinOps report; weekly Step Functions cycle | `feature/llmops-agent` | ❌ Pending |

### 3d — Guardrails, Tools & Prompts

| ID | Task | Branch | Status |
|----|------|--------|--------|
| AF-046 | 6-stage Guardrails Pipeline — OPA policy, Presidio PII + Llama Guard input, prompt constraint validators, tool schema + cost-cap execution guard, TruLens + citation output guard, Evidently AI monitoring; immutable audit log | `feat/platform/guardrails-tool-registry` | ✅ Completed (MVP; real services = Phase-2 follow-up) |
| AF-047 | Tool Registry shell — `ToolRegistry` singleton (register/get/call, JSON-schema + Pydantic validation, auth scope, cost class). Per-pillar tool *entries* (Tavily, GitHub, Stripe, …) remain each pillar's job | `feat/platform/guardrails-tool-registry` | ✅ Completed |
| AF-048 | Prompt Registry — versioned Jinja2 templates in `prompt_registry` table + S3; `get()` resolves active/canary; deterministic canary split; strict variable validation; all agent prompt templates | `feature/prompt-registry` | ❌ Pending |
| AF-049 | LiteLLM Model Router + RAG Pipeline — task-class → model routing rules (Gemini 3.5 Flash for all tasks; gemini-embedding-2 768-dim for all collections); hybrid BM25 + ANN retrieval on Supabase pgvector; Cohere reranking; context compression; citation check | `feature/model-router-rag` | ❌ Pending |
| AF-050 | Eval harness — Promptfoo golden sets per agent, LangSmith batch eval runner, CI gate blocking prompt promotion on score regression > 2% | `feature/eval-harness` | ❌ Pending |

---

## Phase 4 — Frontend (Next.js 14)

> Founder Portal with all 7 pillar surfaces, real-time log streaming, HITL gate UI, and admin dashboard.
> **Depends on: Phase 3**

| ID | Task | Branch | Status |
|----|------|--------|--------|
| AF-051 | Next.js 14 App Router setup — TypeScript strict, Tailwind CSS, shadcn/ui, Supabase Auth `@supabase/supabase-js` + `@supabase/ssr`, global error boundary + Sentry | `feature/nextjs-setup` | ❌ Pending |
| AF-052 | Typed API client (`lib/api-client.ts`) + Supabase Realtime hook (`lib/realtime-client.ts`) — `useRun()` merging React Query + Supabase Realtime channel events, `useGate()` polling + mutation | `feature/api-client-hooks` | ❌ Pending |
| AF-053 | Zustand stores + React Query config — `runStore`, `gateStore`, `uiStore`; responsive layout shell with live cost ticker | `feature/state-management` | ❌ Pending |
| AF-054 | Idea Intake surface — multi-modal form (text, PDF upload, voice record, URL), locale selector, `POST /v1/ideas`, redirect to run page | `feature/idea-intake-ui` | ❌ Pending |
| AF-055 | Validation Studio (Pillar 1) — Lean Canvas viewer, viability gauge 0–100, ICP persona cards, pivot picker, approve/pivot HITL gate UI | `feature/validation-studio` | ❌ Pending |
| AF-056 | Architecture Studio (Pillar 2) — Mermaid ERD renderer, Swagger UI OpenAPI viewer, stack summary card, cost forecast, approve/reject HITL gate UI | `feature/architecture-studio` | ❌ Pending |
| AF-057 | Code Review Studio (Pillar 3–4) — Monaco diff viewer, Reviewer Agent comments panel, self-heal cycle progress indicator, security scan results table | `feature/code-review-studio` | ❌ Pending |
| AF-058 | Deploy Console (Pillar 5) — live deployment log stream, infra-spend HITL gate, smoke test result card, live URL badge, 1-click rollback | `feature/deploy-console` | ❌ Pending |
| AF-059 | Launch Control Center (Pillar 6) — brand kit preview, landing page iframe, social post drafts with edit-in-place, email sequence preview, approve/edit HITL gate; no asset publishes without founder sign-off | `feature/launch-control-center` | ❌ Pending |
| AF-060 | LLMOps Dashboard (Pillar 7) — cost by model/pillar/run chart, drift score time-series, eval score history, prompt version table with canary indicator | `feature/llmops-dashboard` | ❌ Pending |
| AF-061 | Run List / Dashboard — all runs with status, pillar, cost, created date; filter and search; skeleton loaders | `feature/run-dashboard` | ❌ Pending |
| AF-062 | Admin Dashboard — tenant CRUD, model registry management, prompt registry lifecycle, tool registry, audit log viewer, platform FinOps view | `feature/admin-dashboard` | ❌ Pending |

---

## Phase 5 — Mobile (Expo React Native)

> Founder-on-the-go: idea submission, run monitoring, live HITL gate approvals, and push notifications.
> **Depends on: Phase 3**

| ID | Task | Branch | Status |
|----|------|--------|--------|
| AF-063 | Expo Router scaffold — TypeScript strict, Supabase Auth (`@supabase/supabase-js` + `ExpoSecureStoreAdapter`), secure token storage in `expo-secure-store`, shared API client from `packages/shared` | `feature/expo-setup` | ❌ Pending |
| AF-064 | Push notifications — Expo Push Notifications → SNS → realtime WebSocket service; deep-link on tap to relevant gate or run screen | `feature/push-notifications` | ❌ Pending |
| AF-065 | Idea Intake screen — text input, voice record (Expo AV), file attach; submit to `POST /v1/ideas` | `feature/mobile-idea-intake` | ❌ Pending |
| AF-066 | Run Dashboard screen — live run list with status badges and cost; pull-to-refresh; real-time WebSocket updates | `feature/mobile-run-dashboard` | ❌ Pending |
| AF-067 | Run Detail screen — current pillar progress, step log stream, active gate banner | `feature/mobile-run-detail` | ❌ Pending |
| AF-068 | HITL Gate Approval screens — gate-specific review UI (Lean Canvas, Architecture summary, Launch preview); approve/reject with optional note; offline queue + sync on reconnect | `feature/mobile-gate-approval` | ❌ Pending |
| AF-069 | Artifacts Viewer — browse generated outputs (canvas, ERD image, live URL, brand kit, social posts) | `feature/mobile-artifacts-viewer` | ❌ Pending |
| AF-070 | LLMOps Summary screen — cost card, eval score card, last drift check; dark/light mode following system preference | `feature/mobile-llmops-summary` | ❌ Pending |
| AF-071 | EAS Build + release pipeline — `eas.json` profiles (development, preview, production); App Store + Google Play submit via `eas submit` | `feature/eas-build-pipeline` | ❌ Pending |

---

## Phase 6 — VS Code Extension

> In-editor AI co-founder: run monitoring, HITL gate approvals, and code generation commands without leaving the IDE.
> **Depends on: Phase 3**

| ID | Task | Branch | Status |
|----|------|--------|--------|
| AF-072 | Extension core — activation event, command palette scaffold, `vscode.ExtensionContext` lifecycle, Supabase Auth PKCE flow with token stored in `SecretStorage` | `feature/vscode-extension` | ✅ Completed |
| AF-073 | Sidebar tree view — run list with status icons, pillar progress, live cost badge; refreshes via WebSocket subscription | `feature/vscode-extension` | ✅ Completed |
| AF-074 | HITL gate notifications — VS Code notification banner on `gate.required` event; inline approve/reject action buttons | `feature/vscode-extension` | ✅ Completed |
| AF-075 | Code generation commands — `AutoFounder: Generate Component`, `AutoFounder: Generate API Endpoint`; invokes Coder Agent, streams tokens into a new editor tab | `feature/vscode-extension` | ✅ Completed |
| AF-076 | Live token streaming panel — `WebviewPanel` rendering agent step log stream in real time; follows active run | `feature/vscode-extension` | ✅ Completed |
| AF-077 | Artifact quick-open — `AutoFounder: Open Lean Canvas`, `Open ERD`, `Open OpenAPI spec`; fetches from `GET /v1/runs/{id}/artifacts` and previews in editor | `feature/vscode-extension` | ✅ Completed |
| AF-078 | Extension marketplace packaging — `vsce package`, `vsce publish` pipeline in GitHub Actions; auto-bump version on merge to `main` | `feature/vscode-extension` | ✅ Completed |

---

## Dependency Graph

```
Phase 1 — Monorepo & Boilerplate (✅ Done)
    │
    ▼
Phase 2 — Infrastructure & Cloud
    │
    ▼
Phase 3 — Backend (FastAPI + Agents)
    │
    ├──────────────────┬────────────────────┐
    ▼                  ▼                    ▼
Phase 4          Phase 5              Phase 6
Frontend         Mobile               VS Code
(Next.js 14)     (Expo RN)            Extension

Phase 4, 5, 6 are independent of each other — can be parallelised once Phase 3 API contracts are stable.
Phase 3 sub-phases: 3a (API + DB) → 3b (Orchestrator) → 3c (Agents) → 3d (Guardrails + Tools)
```

### Critical Path

`AF-011` → `AF-012–AF-024` → `AF-025–AF-032` → `AF-033–AF-035` → `AF-036–AF-045` → `AF-046–AF-050` → `AF-051–AF-062`

### Parallel Tracks (after AF-050)

| Track | Tasks |
|-------|-------|
| Frontend | AF-051 → AF-062 |
| Mobile | AF-063 → AF-071 |
| VS Code Extension | AF-072 → AF-078 |

---

## Changelog

| Date | Version | Author | Description |
|------|---------|--------|-------------|
| 2026-06-07 | 1.4.0 | Vishal | Mark Phase 6 AF-072 → AF-078 as ✅ Completed — full VS Code extension (core+PKCE auth, sidebar, gate notifications, code-gen, streaming panel, artifact quick-open, `vsce` publish workflow) on `feature/vscode-extension`; wired into pnpm workspace; tsc+ESLint+Prettier clean, 35 unit tests, `vsce package` verified. |
| 2026-06-06 | 1.3.0 | Somesh | Mark AF-036 to AF-039 as ✅ Completed (BaseAgent, Strategy, Research, Product Planner agents shipped on somesh-feature) |
| 2026-06-06 | 1.2.0 | Team | Mark AF-032 to AF-035 as ✅ Completed (delegated to Somesh) |
| 2026-05-20 | 1.0.0 | Team | Initial TASKS.md — 74 tasks across 6 phases; Phase 1 marked complete from existing monorepo scaffold |
| 2026-05-26 | 1.1.0 | Team | Tech stack alignment: Supabase (PostgreSQL + pgvector + Realtime) replaces RDS + MongoDB Atlas + Go WebSocket; Gemini 3.5 Flash replaces Claude Sonnet / GPT-4o; Supabase Auth replaces Auth0; Confluent Kafka added as primary event bus; SQLAlchemy replaces Prisma |
| 2026-06-04 | 1.1.1 | Team | Count fix: Phase 3 corrected 22 → 26 (3a 8 + 3b 3 + 3c 10 + 3d 5); total 74 → 78 (AF-001…AF-078). Now matches `task_assigned.md`. |