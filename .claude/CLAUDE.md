# CLAUDE.md — AutoFounder AI

> This file provides project context, architecture guidance, and conventions for Claude Code agents working on the AutoFounder AI platform. Read this before writing any code, modifying any agent, or making infrastructure changes.

> **This file is a lean index.** The detailed reference now lives in [`.claude/specs/`](specs/). Section numbers are non-contiguous below because the detail sections were extracted — use the spec map to find them.


## 1. Executive Summary

AutoFounder AI is a **multi-tenant, agentic AI SaaS platform** that converts a single text idea into a fully validated, designed, built, tested, deployed, marketed, and continuously-improved software business — autonomously.

It is delivered as a **10-layer reference architecture** (Input → Orchestration → Agents → Models → Data & Knowledge → Output → Services → Guardrails → Compliance → Observability) running on **AWS (ECS Fargate, multi-AZ VPC)**, orchestrated via **LangGraph**, governed by a **6-stage guardrails pipeline**, and observed via a full **OpenTelemetry + ELK + Prometheus + LangSmith** MLOps stack.


---

## 2. System Overview

- **Product**: AutoFounder AI — Next-Generation Autonomous Startup Creation System.
- **Type**: Multi-tenant AI SaaS, agentic system powered by LLMs + Generative AI.
- **Org**: Euron AutoFounder AI, Bengaluru, Karnataka, India — `product@euron.one`.
- **Tagline**: "A true AI co-founder that gets things done."
- **Four pillars of differentiation**: Multi-Agent Collaboration · Persistent Memory · Secure & Scalable · Multi-Tenant SaaS.
- **Core loop (every agent)**: `Understand → Plan → Execute → Verify → Learn`.

---

## Specification Map

Detailed reference, extracted from this document. Open the relevant spec before working in that area.

| Topic | Spec | Covers |
|---|---|---|
| 10-layer architecture, workflow, components, data & comms flow | [`specs/architecture.md`](specs/architecture.md) | §4, §5, §6, §11, §29, §37 |
| Agent roster, LangGraph orchestration, memory, prompts, tools, RAG | [`specs/agents.md`](specs/agents.md) | §7, §8, §9, §10, §30, §32, §33 |
| Backend, frontend, auth, infra & cloud technology choices | [`specs/stack.md`](specs/stack.md) | §13, §14, §15, §17, §18 |
| REST/WebSocket contract, envelopes, errors, pagination | [`specs/api-design.md`](specs/api-design.md) | §12 |
| Multi-tenant schemas, isolation, Alembic, Redis keys | [`specs/database.md`](specs/database.md) | §19 |
| Third-party services, LLM providers & model routing | [`specs/integrations.md`](specs/integrations.md) | §16, §31, §43 |
| AWS ECS Fargate, Terraform, environments, pipeline | [`specs/deployment.md`](specs/deployment.md) | §27, §28 |
| Expo (React Native) app conventions | [`specs/mobile.md`](specs/mobile.md) | — |
| 6-stage guardrails, compliance, multi-tenancy rules | [`specs/governance.md`](specs/governance.md) | §34, §35, §39 |
| Queues, observability, errors, scaling, performance, cost | [`specs/operations.md`](specs/operations.md) | §20, §21, §22, §23, §24, §25, §26, §36, §38 |
| Business objective, pricing, phases, market, risks, future | [`specs/product.md`](specs/product.md) | §3, §44, §45, §45b, §46, §47, §49 |
| Reconciliations vs prior design (authoritative decisions) | [`specs/decisions.md`](specs/decisions.md) | §48 |

---

## 40. Repository Structure (canonical)

```
autofounder-ai/
├── backend/          # FastAPI — consolidated backend (Python; uv)
│   ├── app/
│   │   ├── api/v1/               # REST routes (health, ideas, runs)
│   │   ├── core/                # config, logging, security
│   │   ├── db/                  # UDAL + SQLAlchemy session/base
│   │   ├── models/  schemas/  services/
│   │   ├── agents/              # strategy, research, product_planner (+ base contract)
│   │   ├── orchestrator/        # LangGraph engine
│   │   ├── guardrails/          # 6-stage pipeline
│   │   └── workers/             # queue consumers
│   ├── alembic/                 # database migrations
│   └── tests/
├── frontend/     # Next.js 14 — Founder Portal (+ super-admin `/admin` route group, role-guarded)
├── mobile-app/       # Expo (React Native)
├── infra/            # Terraform + CodeDeploy (AWS ECS Fargate)
│   ├── terraform/
│   └── codedeploy/
├── packages/
│   ├── shared/                  # Shared TypeScript types
│   └── api-client/              # Typed backend client (OpenAPI-generated Phase 2)
├── scripts/                     # setup-dev, deploy-backend-dev (.ps1 + .sh)
├── .github/workflows/           # CI/CD (backend-ci, lint, deploy-frontend)
└── CLAUDE.md                    # ← you are here
```

> **Structure note:** All Python agent / guardrail / tool / prompt / eval code lives under
> `backend/app/`. `packages/` is **TypeScript-only** (`shared`, `api-client`).
> The original `apps/` + per-domain `packages/*` (agents, guardrails, prompts, tools, db, eval)
> layout is retired — see [stack.md](specs/stack.md) and PROJECT-3 convention.

---

## 41. Development Conventions

### Git

- Branches: `feat/<pillar>/<short-description>` (e.g. `feat/engineering/stripe-integration`).
- All changes via PR; no direct push to `main`.
- Conventional Commits.

### Code Quality

- **Frontend (TypeScript)**: strict mode (`"strict": true`); ESLint + Prettier.
- **Backend (Python)**: type hints on all public functions; `mypy` must pass; `ruff` for lint + format.
- All new API routes: matching OpenAPI 3.1 entry (FastAPI auto-generates `/openapi.json`).
- Generated MVPs always include: Dockerfile, docker-compose.yml, GitHub Actions workflow, README, OpenAPI spec.

### Testing

- Unit: Jest (TS), pytest (Python).
- Integration: Playwright (E2E), testcontainers.
- AI evals: LLM-as-judge via LangSmith on every agent output; Promptfoo regression on prompt changes.
- Load: simulate Product Hunt spike before SLA sign-off.

---

## 42. Common Commands

```bash
# Install
pnpm install                                        # JS workspaces
cd backend && uv sync                   # Python backend deps

# Local Supabase (postgres + pgvector + auth + storage + realtime)
supabase start

# Run services locally
pnpm --filter @autofounder-ai/frontend dev      # Next.js Founder Portal
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Docker (ancillary services: Redis)
docker compose up -d

# Quality gates
make quality                                        # backend ruff+mypy+pytest, then JS lint
cd backend && uv run pytest              # backend tests only

# Infra
cd infra/terraform && terraform plan -var-file=env/staging.tfvars

# Evals (Phase 2+) — golden sets live under backend once implemented
```

---

*Lean index generated by `split_claude.py` on 2026-06-04. Full prior version preserved at `CLAUDE.md.backup`.*

