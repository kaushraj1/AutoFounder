# Tech Stack Spec — AutoFounder AI

> Decisions made, the reasoning behind them, and the constraints they impose.
> Update this file when a decision changes — record the old choice and why it changed.
<<<<<<< HEAD
=======
>
> **Authoritative source**: `CLAUDE.md §13, §14, §15, §17, §18`
>>>>>>> dev

---

## Backend

### Language — Python 3.12

**Why**: The entire agent/ML ecosystem (LangGraph, LangChain, LlamaIndex, DSPy, TruLens,
Evidently, Promptfoo bindings) is Python-native. Calling these from any other language
requires subprocess bridging or HTTP round-trips, both of which add latency and operational
complexity on the hot agent execution path.

**Constraints**:
<<<<<<< HEAD
- All public functions must have type hints. `mypy` (or Pyright) runs in CI.
- Python version is pinned in `pyproject.toml` (`requires-python = ">=3.12"`). Do not widen without a team decision.
=======
- All public functions must have type hints. `mypy` runs in CI.
- Python version is pinned in `pyproject.toml` (`requires-python = ">=3.12"`).
>>>>>>> dev

### Framework — FastAPI

**Why**: Async-native (ASGI), Pydantic v2 request/response validation built in, OpenAPI 3.1
spec auto-generated from code, excellent integration with `asyncio`-based agent executors.

**Constraints**:
<<<<<<< HEAD
- Every route is `async def`. Sync blocking calls (file I/O, heavy CPU) go into `asyncio.to_thread`.
=======
- Every route is `async def`. Sync blocking calls go into `asyncio.to_thread`.
>>>>>>> dev
- Pydantic models use `model_config = ConfigDict(strict=True)` — no implicit coercion.
- OpenAPI spec (`openapi.yaml`) stays in sync. CI lints the spec against route definitions.

### Package Manager — uv

<<<<<<< HEAD
**Why**: Drops pip + venv + pip-tools into a single binary. Deterministic lockfile (`uv.lock`).
10–100× faster than pip. Integrates with `pyproject.toml` — no separate `requirements.txt`.

**Commands**:
=======
**Why**: Single binary replacing pip + venv + pip-tools. Deterministic lockfile (`uv.lock`).
10–100× faster than pip. Integrates with `pyproject.toml`.

>>>>>>> dev
```bash
uv sync --all-groups       # install all deps including dev
uv add <package>           # add runtime dep
uv add --dev <package>     # add dev dep
uv run pytest              # run in managed venv
```

### Linting & Formatting — Ruff

<<<<<<< HEAD
**Why**: Single binary replacing Flake8 + isort + pyupgrade + pydocstyle + Black. Same
line-length, same import sorting, zero config drift between tools.

**Config** (`pyproject.toml`):
- `line-length = 100`
- `select = ["E", "F", "I", "UP", "B"]` — errors, Pyflakes, isort, upgrades, bugbear
=======
**Why**: Single binary replacing Flake8 + isort + pyupgrade + Black. Zero config drift.

**Config** (`pyproject.toml`):
- `line-length = 100`
- `select = ["E", "F", "I", "UP", "B"]`
>>>>>>> dev
- CI fails on any lint or format violation. Auto-fix with `make backend-format`.

### LLM Orchestration — LangGraph

<<<<<<< HEAD
**Why**: Stateful DAGs with native HITL interrupt support, Postgres + Redis checkpointing out of the box,
and first-class streaming. The alternative (Celery task graphs) lacks native state, requires custom
checkpointing, and has no concept of human-in-the-loop pausing.
=======
**Why**: Stateful DAGs with native HITL interrupt support, Postgres + Redis checkpointing out
of the box, and first-class streaming.
>>>>>>> dev

**Constraints**:
- Every `StateGraph` node must call `learn(trace)` at exit — traces feed LLMOps.
- Checkpoints are written to Postgres (`orchestrator.checkpoints`) AND Redis (hot cache).
<<<<<<< HEAD
- AutoGen is the fallback for free-form multi-agent chat steps only; LangGraph is the orchestrator for structured pillar execution.
=======
- AutoGen is the fallback for free-form multi-agent chat steps only.
>>>>>>> dev

---

## Frontend — Web

<<<<<<< HEAD
### Framework — React + TypeScript + Vite

**Why**: React for component model; Vite for fast HMR and native ESM dev server; TypeScript strict
mode catches prop/state bugs at build time.

**Constraints**:
- `"strict": true` in `tsconfig.json` — no implicit `any`.
- Components are named exports in PascalCase files.
- No default exports for components (makes refactoring and tree-shaking predictable).

### Styling — Tailwind CSS + shadcn/ui

**Why**: Tailwind eliminates dead CSS; shadcn/ui provides accessible, unstyled primitives that
compose into the design system without a runtime CSS-in-JS penalty.

**Constraints**:
- No inline `style={{}}` except for values computed at runtime (e.g. dynamic widths from data).
- No custom re-implementations of shadcn/ui primitives (Button, Input, Modal, etc.).
- Design tokens live in `tailwind.config.ts` — not hardcoded hex values in class names.

### State — React Query + Zustand
=======
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
>>>>>>> dev

| Concern | Tool |
|---------|------|
| Server data (API responses, caching, refetch) | React Query |
| UI-only state (open/close, active tab, theme) | Zustand |
<<<<<<< HEAD
| Real-time updates (run logs, gate events) | WebSocket hook merged into React Query cache |

### Build Tool — Turborepo (monorepo orchestration)

**Why**: Turborepo caches task outputs across packages. `turbo lint` on a PR only re-lints packages
that changed. `turbo build` parallelises across `frontend-web`, `mobile-app`, `vscode-extension`.
=======
| Real-time updates (run logs, gate events) | Supabase Realtime channel merged into React Query cache |

### Auth — Supabase Auth

`@supabase/supabase-js` + `@supabase/ssr` for the Next.js integration.
JWT stored in an httpOnly cookie managed by the Supabase SSR helper.
MFA enforced for all human accounts.
>>>>>>> dev

---

## Mobile — Expo (React Native)

<<<<<<< HEAD
**Why**: Single TypeScript codebase compiles to iOS + Android. EAS Build provides managed cloud
builds without macOS CI runners for Android. EAS Submit automates App Store and Play Store delivery.
Expo modules (Camera, AV, Notifications, SecureStore) cover all AutoFounder AI mobile use cases.
=======
**Why**: Single TypeScript codebase compiles to iOS + Android. EAS Build provides managed
cloud builds without macOS CI runners for Android. Expo modules cover all mobile use cases.
>>>>>>> dev

**Constraints**:
- Expo SDK version is pinned. Do not upgrade mid-sprint.
- All secrets stored in `expo-secure-store` — never `AsyncStorage` for tokens.
<<<<<<< HEAD
=======
- Auth via Supabase Auth (`@supabase/supabase-js` + `ExpoSecureStoreAdapter`).
>>>>>>> dev
- OTA updates (Expo Updates) for JS-only changes; new native modules require a full EAS build.

---

## VS Code Extension — TypeScript + VS Code API

**Why**: Direct VS Code extension API access (SecretStorage, TreeView, WebviewPanel, commands,
<<<<<<< HEAD
notifications). TypeScript gives type safety for the API surface.

**Constraints**:
- Activation events must be specific — not `onStartupFinished` for the whole extension.
=======
notifications). TypeScript gives type safety for the full API surface.

**Constraints**:
- Activation events must be specific.
>>>>>>> dev
- Long-running operations use `vscode.window.withProgress`.
- Auth tokens stored in `vscode.SecretStorage`, never `globalState`.

---

## Infrastructure

<<<<<<< HEAD
### Cloud — GCP + Terraform

**Why**: GCP's managed services (Cloud SQL, Memorystore, Cloud Run, Pub/Sub, Artifact Registry,
Secret Manager) map cleanly to every AutoFounder AI workload. Terraform provides provider-agnostic
IaC syntax and a mature GCP provider.

**Constraints**:
- No AWS or Azure SDKs. If a library hard-requires AWS, find a GCP alternative or wrap it.
- Every GCP resource is tagged with `env`, `project`, `managed-by = "terraform"`.
- Terraform state lives in a GCS backend bucket — never committed to git.

### Compute — Cloud Run (primary)

**Why**: Fully managed, scales to zero, supports HTTP/2 (gRPC), and handles container concurrency
natively. No cluster management overhead. Agent worker tasks that need ephemeral sandboxes use
Cloud Run Jobs (one-off invocations).

**Trade-off**: Cold start latency (~1–3 s) is acceptable for the agent pipeline; unacceptable for
the FastAPI gateway. The gateway service uses `min-instances = 1` to keep one warm instance.

### Databases — PostgreSQL 16 + Redis 7

**Why**:
- PostgreSQL: ACID, JSONB for plan DAGs, Alembic migrations, schema-per-tenant isolation, RLS.
- Redis: sub-millisecond cache, LangGraph checkpoint hot path, Pub/Sub for gate events, rate-limit counters.

**GCP services**: Cloud SQL (PostgreSQL 16, HA replica), Memorystore for Redis.

**Local dev**: Docker Compose (`make stack`) — same major versions as production.
=======
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
>>>>>>> dev

### Monorepo — pnpm + Turborepo

**Workspace packages** (from `pnpm-workspace.yaml`):
<<<<<<< HEAD
- `frontend-web`
- `mobile-app`
- `vscode-extension`

Backend (`backend/`) is **not** a pnpm workspace — it is a Python project managed by `uv`.
Turborepo orchestrates JS/TS tasks only; backend tasks run via `Makefile`.

---

## Decisions Still Open

| Decision | Options | Blocker |
|----------|---------|---------|
| Vector store | Vertex AI Vector Search vs Pinecone vs MongoDB Atlas | GCP-native preference but cost model unclear |
| Graph DB | Neo4j AuraDB vs AlloyDB Graph vs self-managed | Benchmark needed |
| Primary LLM | Gemini (GCP-native, lower egress cost) vs Claude Sonnet vs GPT-4o | Eval results pending |
| Feature flags | GrowthBook (self-hosted) vs LaunchDarkly vs Statsig | Budget |
| GCP region | `asia-south1` (Mumbai) only vs multi-region from day one | Traffic distribution data needed |
=======
- `apps/web`
- `apps/admin`
- `packages/shared`
- `packages/eval`

Python services (`apps/api`, `apps/orchestrator`, `apps/ai-services`) are managed by `uv` —
not pnpm workspaces. Turborepo orchestrates JS/TS tasks only; Python tasks run via `Makefile`.

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
>>>>>>> dev
