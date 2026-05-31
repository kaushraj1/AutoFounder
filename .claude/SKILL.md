---
name: autofounder-ai-dev
description: Development skill for AutoFounder AI — a multi-tenant agentic AI SaaS that turns a text idea into a deployed software business, built on FastAPI, Next.js 14, Expo, VS Code Extension, Supabase (PostgreSQL + pgvector + Storage + Realtime), Redis (ElastiCache), Confluent Kafka, Gemini 3.5 Flash, and AWS Terraform (ECS Fargate).
---

# AutoFounder AI — Dev Skill

Use this skill whenever you are writing, reviewing, or modifying code in the `autofounder-ai` monorepo.
It tells you what to read first, which conventions to follow, which checklists to run before handing
off a change, and what is explicitly off-limits without a human approval gate.

---

## Canonical Sources — Read in This Order

1. **`CLAUDE.md`** (project root) — full architecture reference: 10-layer system, agent roster, HITL
   gates, memory tiers, guardrails pipeline, performance SLAs, multi-tenancy rules.
2. **`.claude/MEMORY.md`** — quick-reference: product identity, stack decisions, directory layout,
   key commands, branch strategy, open questions.
3. **`.claude/TASKS.md`** — phase/task tracker: current status per task ID (AF-001 … AF-078),
   dependency order, what is and isn't built yet.

If any of these files contradict each other, `CLAUDE.md` is authoritative.

---

## When This Skill Applies

Activate this skill for any of the following:

- **FastAPI routes** — adding or modifying endpoints in `backend/src/`
- **LangGraph nodes / agents** — any file under the agent layer (Strategy, Architect, Coder, Reviewer,
  DevOps, Marketing, LLMOps and sub-agents)
- **React components** — new UI in `frontend-web/src/` (Founder Portal surfaces or admin)
- **Vite config changes** — `vite.config.ts`, aliasing, env handling, bundle splits
- **PostgreSQL migrations** — Alembic revision files in `backend/`
- **Redis key design** — new cache keys, TTL policy, or pub/sub channels
- **Terraform modules** — anything under `infra/` targeting AWS resources
- **Expo screens or hooks** — `mobile-app/src/` screens, navigation, or native integrations
- **VS Code extension** — commands, webviews, tree providers in `vscode-extension/src/`
- **Guardrails pipeline** — any of the 6 stages, OPA policies, audit log writes
- **Prompt templates** — Jinja2 templates in the prompt registry
- **UDAL / data layer** — `packages/db/` Python or TypeScript UDAL clients
- **CI/CD workflows** — `.github/workflows/` changes affecting build, test, or deploy

---

## Operating Principles

### 1 — Vertical Slices
Deliver one complete, working slice at a time: migration → UDAL method → FastAPI route → React hook →
UI component. Do not leave half-open layers (e.g. a route with no migration backing it, or a component
that calls an endpoint that doesn't exist yet).

### 2 — Multi-Tenant Safety
Every database query must go through the UDAL with a resolved `tenant_id`. Direct use of SQLAlchemy
sessions, `psycopg`, or any DB driver outside `packages/db/` is **forbidden**. Every new route must
extract `tenant_id` from the verified JWT before touching data.

### 3 — AWS-First Infrastructure
Default to managed AWS services (ECS Fargate, ElastiCache, Supabase for DB/vector/storage, Confluent Kafka, ECR, Secrets Manager, S3).
Do not introduce GCP or Azure SDK dependencies. Terraform modules go in `infra/modules/<service>/`.
Every new AWS resource needs a corresponding IAM binding with least-privilege roles (no wildcard `*:*`).

### 4 — Observability Is Not Optional
Every new FastAPI route must emit a structured log entry (including `tenant_id`, `run_id` where
applicable) and increment at least one Prometheus counter or histogram. Every new LangGraph node must
call `learn(trace)` to push execution traces to the LLMOps agent via Confluent Kafka / EventBridge.

### 5 — Third-Party / Webhook Safety
All outbound tool calls go through the Tool Registry with schema validation and rate-limit checks from
Execution Guardrail (Stage 4) applied before the call is made. Never make a raw `httpx` / `requests`
call to an external API from agent code. Inbound webhooks (Stripe, GitHub, social APIs) must validate
signatures before processing.

### 6 — No Hard-Coded Values
Secrets belong in AWS Secrets Manager (accessed via the Secrets module). Config belongs in SSM Parameter
Store / environment variables injected at deploy time. `semgrep` will block any hard-coded API key,
password, or connection string committed to the repo.

---

## Implementation Checklists

### New REST Endpoint (FastAPI)

- [ ] Route added to the correct router in `backend/src/autofounder-ai/routers/`
- [ ] Request and response shapes defined as Pydantic v2 models with `model_config = ConfigDict(strict=True)`
- [ ] `tenant_id` extracted from JWT dependency before any UDAL call
- [ ] UDAL used for all DB reads/writes — no raw driver calls
- [ ] Happy-path and error cases return the standard envelope `{data, error, requestId}`
- [ ] Route registered in OpenAPI 3.1 spec (`openapi.yaml`) — description, tags, request/response schemas
- [ ] Unit test in `backend/tests/` covering happy path + auth failure + 404
- [ ] Structured log line emitted (at minimum `INFO` with `tenant_id`, `route`, `duration_ms`)
- [ ] `make quality` passes locally before opening PR

### New React Component (frontend-web)

- [ ] Component file in `frontend-web/src/components/<Surface>/` — PascalCase filename, named export
- [ ] Props typed with a dedicated `interface <Name>Props` — no `any`
- [ ] Data fetching via React Query (`useQuery` / `useMutation`) — no raw `fetch` in components
- [ ] Real-time data merged from WebSocket hook (`useRun` / `useGate`) where applicable
- [ ] Loading, empty, and error states all handled — no silent blank renders
- [ ] Tailwind classes only — no inline styles, no `style={{}}` except for dynamic values
- [ ] `shadcn/ui` primitives used for buttons, inputs, modals — no custom re-implementations
- [ ] Component is accessible: ARIA labels on interactive elements, keyboard navigable
- [ ] `pnpm lint` passes in `frontend-web/`

### New Database Migration (Alembic)

- [ ] Generate with `uv run alembic revision --autogenerate -m "<short description>"` in `backend/`
- [ ] Review auto-generated file — remove any destructive ops (`DROP TABLE`, `DROP COLUMN`) not explicitly intended
- [ ] `upgrade()` and `downgrade()` both implemented and tested locally
- [ ] New table: `tenant_id` column present with an index; RLS policy added as defense-in-depth
- [ ] New column on existing table: nullable or has a server-side default — never a bare `NOT NULL` without default on a non-empty table
- [ ] Migration file committed alongside the application code that depends on it — never migrate without the code or vice versa
- [ ] `platform` schema changes (tenants, model_registry, etc.) in a separate migration from tenant-schema changes
- [ ] `make stack` + `uv run alembic upgrade head` runs cleanly from a fresh Docker volume

### New Terraform Module (AWS)

- [ ] Module directory: `infra/modules/<service>/` with `main.tf`, `variables.tf`, `outputs.tf`
- [ ] All resource names include `${var.environment}` and `${var.aws_region}` — no hard-coded names
- [ ] IAM policies follow least-privilege: use specific actions, never wildcard `*:*`
- [ ] Sensitive outputs (connection strings, keys) marked `sensitive = true`
- [ ] `terraform fmt` and `terraform validate` pass
- [ ] `terraform plan` output reviewed and attached to PR description
- [ ] Secrets stored in AWS Secrets Manager (not SSM for sensitive values); referenced by ARN in task definitions
- [ ] Module consumed in `infra/env/staging/main.tf` and `infra/env/production/main.tf` with separate `.tfvars` files

---

## Out of Scope Without Explicit Approval

The following require a human decision before any code is written:

- Changing the tenant isolation strategy (schema-per-tenant, RLS, or otherwise)
- Adding a new cloud provider (AWS, Azure) or moving off GCP
- Replacing the LangGraph orchestration layer with a different framework
- Modifying the 6-stage Guardrails pipeline in a way that removes or weakens any stage
- Introducing a new primary LLM provider (beyond the current Gemini 3.5 Flash routing via LiteLLM)
- Schema changes to `platform.audit_log` — this table is compliance-critical
- Any change to authentication flows (Supabase Auth config, JWT claims structure, MFA policy)
- Generating or committing secrets, certificates, or service-account keys of any kind

---

## Handoff

When a task is complete, summarise:
1. **Files changed** — list every file touched with a one-line description of the change
2. **Commands to verify** — exact `make` / `pnpm` / `uv` commands the next agent or developer should run
3. **Open items** — anything intentionally deferred, with the task ID it maps to in `TASKS.md`
<<<<<<< HEAD
4. **Follow-on tasks** — any new `AF-XXX` tasks that should be added to `TASKS.md` as a result of this work
=======
4. **Follow-on tasks** — any new `AF-XXX` tasks that should be added to `TASKS.md` as a result of this work
>>>>>>> dev
