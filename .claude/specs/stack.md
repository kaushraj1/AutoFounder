# Tech Stack Spec — AutoFounder AI

> Decisions made, the reasoning behind them, and the constraints they impose.
> Update this file when a decision changes — record the old choice and why it changed.
>
> **Authoritative source**: `CLAUDE.md §13, §14, §15, §17, §18`

---

## Backend

### Language — Python 3.12

**Why**: The entire agent/ML ecosystem (LangGraph, LangChain, LlamaIndex, DSPy, TruLens,
Evidently, Promptfoo bindings) is Python-native. Calling these from any other language
requires subprocess bridging or HTTP round-trips, both of which add latency and operational
complexity on the hot agent execution path.

**Constraints**:
- All public functions must have type hints. `mypy` runs in CI.
- Python version is pinned in `pyproject.toml` (`requires-python = ">=3.12"`).

### Framework — FastAPI

**Why**: Async-native (ASGI), Pydantic v2 request/response validation built in, OpenAPI 3.1
spec auto-generated from code, excellent integration with `asyncio`-based agent executors.

**Constraints**:
- Every route is `async def`. Sync blocking calls go into `asyncio.to_thread`.
- Pydantic models use `model_config = ConfigDict(strict=True)` — no implicit coercion.
- OpenAPI spec (`openapi.yaml`) stays in sync. CI lints the spec against route definitions.

### Package Manager — uv

**Why**: Single binary replacing pip + venv + pip-tools. Deterministic lockfile (`uv.lock`).
10–100× faster than pip. Integrates with `pyproject.toml`.

```bash
uv sync --all-groups       # install all deps including dev
uv add <package>           # add runtime dep
uv add --dev <package>     # add dev dep
uv run pytest              # run in managed venv
```

### Linting & Formatting — Ruff

**Why**: Single binary replacing Flake8 + isort + pyupgrade + Black. Zero config drift.

**Config** (`pyproject.toml`):
- `line-length = 100`
- `select = ["E", "F", "I", "UP", "B"]`
- CI fails on any lint or format violation. Auto-fix with `make backend-format`.

### LLM Orchestration — LangGraph

**Why**: Stateful DAGs with native HITL interrupt support, Postgres + Redis checkpointing out
of the box, and first-class streaming.

**Constraints**:
- Every `StateGraph` node must call `learn(trace)` at exit — traces feed LLMOps.
- Checkpoints are written to Postgres (`orchestrator.checkpoints`) AND Redis (hot cache).
- AutoGen is the fallback for free-form multi-agent chat steps only.

---

## Frontend — Web

### Framework — Next.js 14 (App Router)

**Why**: Server-side rendering + React Server Components reduce the Founder Portal's initial
load time. App Router gives file-system routing, nested layouts, and streaming SSR.
Tailwind + shadcn/ui deliver the design system without a runtime CSS-in-JS penalty.

**Constraints**:
- `"strict": true` in `tsconfig.json` — no implicit `any`.
- App Router only — no Pages Router.
- Server components for data-fetching pages; client components only where interactivity is
  required (use `"use client"` directive explicitly).
- No default exports for components (makes tree-shaking and refactoring predictable).

### Styling — Tailwind CSS + shadcn/ui

**Why**: Tailwind eliminates dead CSS; shadcn/ui provides accessible, unstyled primitives.

**Constraints**:
- No inline `style={{}}` except for truly runtime-computed values.
- No custom re-implementations of shadcn/ui primitives.
- Design tokens live in `tailwind.config.ts` — not hardcoded hex values in class names.

### State — React Query + Zustand + Supabase Realtime

| Concern | Tool |
|---------|------|
| Server data (API responses, caching, refetch) | React Query |
| UI-only state (open/close, active tab, theme) | Zustand |
| Real-time updates (run logs, gate events) | Supabase Realtime channel merged into React Query cache |

### Auth — Supabase Auth

`@supabase/supabase-js` + `@supabase/ssr` for the Next.js integration.
JWT stored in an httpOnly cookie managed by the Supabase SSR helper.
MFA enforced for all human accounts.

---

## Mobile — Expo (React Native)

**Why**: Single TypeScript codebase compiles to iOS + Android. EAS Build provides managed
cloud builds without macOS CI runners for Android. Expo modules cover all mobile use cases.

**Constraints**:
- Expo SDK version is pinned. Do not upgrade mid-sprint.
- All secrets stored in `expo-secure-store` — never `AsyncStorage` for tokens.
- Auth via Supabase Auth (`@supabase/supabase-js` + `ExpoSecureStoreAdapter`).
- OTA updates (Expo Updates) for JS-only changes; new native modules require a full EAS build.

---

## VS Code Extension — TypeScript + VS Code API

**Why**: Direct VS Code extension API access (SecretStorage, TreeView, WebviewPanel, commands,
notifications). TypeScript gives type safety for the full API surface.

**Constraints**:
- Activation events must be specific.
- Long-running operations use `vscode.window.withProgress`.
- Auth tokens stored in `vscode.SecretStorage`, never `globalState`.

---

## Infrastructure

### Cloud — AWS + Terraform

**Why**: AWS ECS Fargate gives fully managed container hosting without Kubernetes cluster
management overhead. Terraform provides mature AWS provider support and readable IaC syntax.
Multi-AZ private subnets ensure HA without complexity.

**Constraints**:
- Deployment target is **Amazon ECS on Fargate** — not EKS, not EC2, not Lambda for stateful services.
- Every AWS resource tagged with `env`, `project`, `managed-by`, `team`.
- Terraform state in S3 backend (versioned) + DynamoDB lock table.
- No wildcard `*:*` IAM policies — least-privilege per ECS task role.

### Compute — ECS Fargate

**Why**: Fully managed, multi-AZ, no cluster/node management. Agent worker tasks that need
ephemeral sandboxes use `run_task` (one-off Fargate invocations).

**Trade-off**: Fargate cold-start (~5–15 s) is acceptable for agent steps; unacceptable for the
API gateway. The `api` and `web` services use `min tasks = 2` to keep warm instances in both AZs.

### Database — Supabase (PostgreSQL + pgvector)

**Why**: Supabase consolidates relational DB, vector search, auth, file storage, and realtime
into a single hosted platform, eliminating separate RDS + Qdrant/Pinecone + Auth0 + S3
operational overhead.

- PostgreSQL 16 — ACID, JSONB for plan DAGs, Alembic migrations, schema-per-tenant isolation.
- pgvector — `vector(768)` HNSW index for all 7 semantic collections (gemini-embedding-2 dimensions).
- Supabase Realtime — pg_notify-based WebSocket fan-out; frontend subscribes to `step_events` per `run_id`.
- Supabase Auth — OAuth 2.0 + SAML 2.0, short-lived JWTs, MFA.
- Supabase Storage — app artifacts, generated assets.

### Cache — Amazon ElastiCache for Redis 7

- LangGraph plan checkpoints (hot path).
- Semantic prompt cache and embedding cache.
- Per-tenant cost accumulator.
- Rate-limit counters.
- Local dev: Docker Compose Redis 7 (same major version as production).

### Message Bus — Confluent Kafka (primary) + EventBridge + SQS/SNS

| Bus | Role |
|-----|------|
| **Confluent Kafka** | Primary inter-agent events, LLMOps telemetry (high-throughput, ordered) |
| Amazon EventBridge | Schema registry, cross-service routing, `gate.required` events |
| Amazon SQS | Per-pillar work queues + DLQs |
| Amazon SNS | Fan-out (push notifications, webhooks, alerts) |
| AWS Step Functions | Long-running orchestration (weekly LLMOps cycle) |

### Object Storage

| Store | Purpose |
|-------|---------|
| **Supabase Storage** | App artifacts, generated assets, brand kits — accessed by agents and frontend |
| **Amazon S3** | Raw data lake, RLHF datasets, audit logs (7-yr S3 Object Lock), prompt-template immutable archives |

### Monorepo — pnpm + Turborepo (lowercase dirs)

**Workspace members** (from `pnpm-workspace.yaml`):
- `frontend` (`@autofounder-ai/frontend`) — includes the super-admin `/admin` route group
- `mobile-app` (`@autofounder-ai/mobile-app`)
- `backend` (`@autofounder-ai/backend`)
- `packages/shared`, `packages/api-client`

The backend is a **consolidated FastAPI service** (modular monolith): the API gateway, LangGraph
orchestrator, and agent workers live as internal modules under `backend/app/`
(`api/`, `orchestrator/`, `agents/`, `workers/`, …), to be extracted into separate services in
Phase 4 if scale requires. It is managed by `uv`; its `package.json` delegates lint/typecheck/test
to uv so Turborepo can orchestrate JS/TS and Python tasks uniformly. Long-running Python commands
also run via the `Makefile`.

> Convention: **lowercase** top-level app dirs (a deliberate deviation from the org reference repo
> PROJECT-3-AgentOps-Commander, which uses UPPERCASE), one consolidated backend, `packages/*` for
> shared TypeScript only.

---

## Resolved Decisions

| Decision | Resolution |
|----------|-----------|
| Cloud provider | **AWS** (ECS Fargate, multi-AZ VPC, ElastiCache, S3, ECR, Secrets Manager) |
| Vector store | **Supabase pgvector** — `vector(768)` HNSW; eliminates separate vector DB |
| Primary LLM | **Gemini 3.5 Flash** (all task classes via LiteLLM router) |
| Embeddings | **gemini-embedding-2** — 768 dimensions, all 7 collections |
| Auth | **Supabase Auth** — OAuth 2.0, short-lived JWTs, MFA, `SUPABASE_JWT_SECRET` validation |
| Frontend framework | **Next.js 14 App Router** — SSR, RSC, Tailwind + shadcn/ui |
| ORM | **SQLAlchemy (async) + Alembic** migrations |
| Realtime fan-out | **Supabase Realtime** (managed; no separate Go WebSocket service) |
| Message bus | **Confluent Kafka** primary + EventBridge + SQS/SNS |
| Agent contract language | **Python** (not TypeScript) |
| Secrets | **AWS Secrets Manager + SSM Parameter Store** (KMS-encrypted) |
| Tenant isolation | **Schema-per-tenant** in PostgreSQL + RLS as defense-in-depth |

---

## Open Decisions

| Decision | Options | Blocker |
|----------|---------|---------|
| Graph DB | Neo4j AuraDB vs Amazon Neptune | Benchmark on competitor ↔ market ↔ persona queries |
| Feature flags | LaunchDarkly vs GrowthBook vs Statsig | Budget / self-hosting preference |
| Primary AWS region | `ap-south-1` (Mumbai) only vs multi-region from day one | Traffic distribution data needed |
| Mobile platforms for v1 | iOS + Android simultaneously vs iOS-first | Resource capacity |
