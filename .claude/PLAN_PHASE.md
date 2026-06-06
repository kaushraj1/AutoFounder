# Phase Plan — P1: Validation Engine (Active)

> **Drill-down execution plan for the current product phase.** When P1 completes, archive this file's contents into a `phases/` history and replace it with the P2 plan.
>
> **Parent**: `.claude/PLAN.md` · **Architecture**: `.claude/CLAUDE.md` · **Tasks**: `.claude/TASKS.md` · **Owners**: `task_assigned.md`
> **Date**: 2026-06-03 · **Status**: 🟢 Active · **Milestone (M1)**: 10 pilot clients running idea → validated.

---

## 1. Goal

> **Founder submits a text idea → gets a Lean Canvas, viability score (0–100), 3–5 ICPs, competitor analysis, and a PRD — in under 30 minutes — and approves/pivots from the UI.**

This is the thinnest *end-to-end vertical slice* that proves the platform: real auth + multi-tenancy + orchestrator + 3 agents + guardrails + a UI to view and approve results. Pillars 2–7 are **out of scope** for P1.

---

## 2. Scope

### ✅ In scope
- **Foundation**: AWS infra, Supabase migrations, UDAL, FastAPI app, auth, Redis, orchestrator (LangGraph), `BaseAgent`.
- **Shared agent plumbing**: Prompt Registry, LiteLLM Router + RAG, Tool Registry, minimal Guardrails, Eval harness.
- **Pillar-1 agents**: Strategy & Ideation, Research, Product Planner.
- **UI slice**: Idea Intake, live run stream, Validation Studio (Lean Canvas + viability gauge + ICPs + pivot picker + approve gate), PRD viewer, run list.
- **Multi-tenancy + observability + cost tracking** for the above.

### ❌ Out of scope (later product phases)
- Pillars 2–7 agents (Architect, Coder, Reviewer, DevOps, Marketing, LLMOps **agent**) → P2–P4.
- Mobile app (Expo) and VS Code extension → parallel tracks, not required for M1.
- Finance & Ops/Risk agents → P4.

---

## 3. Work Breakdown (the P1 vertical slice → AF tasks)

> Only the tasks needed to ship M1. Full descriptions in `.claude/TASKS.md`; owners in `task_assigned.md`.

### 3.1 Foundation — Owner: **Asit** (critical path)

| AF | Task | Why P1 needs it |
|----|------|-----------------|
| AF-012 → AF-021 | Terraform: networking, ECS, Supabase, ElastiCache, S3, messaging, ALB, IAM, secrets, ECR | Run the platform on AWS |
| AF-022 → AF-024 | CI/CD + OTel + Prometheus/Grafana | Ship safely + see what's happening |
| AF-025, AF-026 | Alembic migrations (platform + per-tenant schemas) | Persist runs, artifacts, gates |
| **AF-027** | **UDAL** ⭐ | Every agent reads/writes tenant-scoped data through it |
| AF-028, AF-029, AF-030 | FastAPI app + auth middleware + REST endpoints (`/v1/ideas`, `/v1/runs/{id}`, gates, artifacts) | The API the UI calls |
| AF-031, AF-032 | Supabase Realtime + Redis | Live run streaming + checkpoints/cache |
| AF-033 → AF-035 | LangGraph `StateGraph` + HITL gate machine + SQS worker | Run the Pillar-1 DAG with the approve/pivot gate |
| **AF-036** | **`BaseAgent` ABC** ⭐ | All 3 Pillar-1 agents subclass this |
| AF-047 | Tool Registry (shell) | Pillar-1 tools register here |

### 3.2 Shared agent plumbing — Owner: **Purnima**

| AF | Task | Why P1 needs it |
|----|------|-----------------|
| AF-048 | Prompt Registry | Versioned Jinja2 templates for the 3 agents |
| AF-049 | LiteLLM Router + RAG | Gemini 3.5 Flash routing + `market_intelligence` retrieval |
| AF-050 | Eval harness | Promptfoo golden sets gate prompt quality |
| AF-046 ⚠️ | Minimal Guardrails (input PII/injection + output) | No raw user text reaches the LLM unfiltered — **owner unassigned, see Part D** |

### 3.3 Pillar-1 agents — Owner: **Somesh**

| AF | Task | Output |
|----|------|--------|
| AF-038 | Research Agent | `{market_signals, competitors[], trends, sources[]}` |
| AF-037 | Strategy & Ideation Agent | Lean Canvas, viability 0–100, 3–5 ICPs, bias audit, 3 pivots (SLA < 30 min) |
| AF-039 | Product Planner Agent | PRD, feature list (MoSCoW), 3-sprint roadmap, user stories (after gate approval) |

### 3.4 UI slice — Owner: **Raunak**

| AF | Task | P1 role |
|----|------|---------|
| AF-051, AF-053 | Next.js 14 setup + Zustand/React Query | App shell |
| AF-052 | Typed API client + Realtime hook | Connects UI to AF-030/AF-031 |
| AF-054 | Idea Intake | Submit idea → `run_id` |
| AF-055 | Validation Studio | Lean Canvas + viability gauge + ICP cards + pivot picker + approve/pivot gate |
| AF-061 | Run List / Dashboard | See all runs + status + cost |

> PRD viewer rides on AF-055/AF-061 surfaces (Monaco read-only) — fold into the Validation Studio slice.

---

## 4. Sprint Plan (6 weeks)

| Sprint | Weeks | Theme | Exit deliverable |
|--------|-------|-------|------------------|
| **S1** | 1–2 | "The Researcher Release" | Foundation up (AF-012→036), `BaseAgent` + Research Agent producing trace logs; `POST /v1/ideas` → `run_id` |
| **S2** | 3–4 | "The Founder Release" | Strategy + Product Planner agents wired; Validation Studio UI live; approve/pivot gate works end-to-end |
| **S3** | 5–6 | "The Agency Release" | Multi-tenancy hardened (two orgs isolated), cost tracking, guardrails + evals green, 10 pilot clients onboarded |

---

## 5. Critical Path & Wiring Order

```
Somesh/Asit: ~~AF-027 UDAL~~ ✅ → AF-036 BaseAgent → ~~AF-028 FastAPI~~ ✅ → ~~AF-030 REST contracts~~ ✅
        │                                   └─ Raunak swaps mock data → real API client (AF-052)
        ▼
Purnima: AF-048 Prompt Registry + AF-049 LLM Router  (+ AF-046 guardrails)
        ▼
Somesh: wire AF-038 Research → AF-037 Strategy → AF-039 Product Planner (subclass BaseAgent, read/write via UDAL)
        ▼
Orchestrator (AF-033) runs the DAG: Research → Strategy → [HITL gate] → Product Planner
```

**Do-now-in-parallel (no foundation needed):**
- **Somesh** — Jinja2 prompts, tool wrappers (Tavily/SerpAPI/Crunchbase/G2/SimilarWeb), Pydantic output schemas, golden eval sets, mocked tests.
- **Purnima** — Eval harness scaffold, router rules, RAG pipeline against test data, prompt-registry loader.
- **Raunak** — all UI screens on mock data + design system.
- **Asit must publish the Pillar-1 I/O Pydantic schemas + OpenAPI 3.1 spec on day 1** so everyone builds against a frozen contract.

---

## 6. Exit Criteria (Definition of Done for P1 / M1)

- [ ] `POST /v1/ideas` accepts a text idea and returns `run_id` in < 500 ms.
- [ ] Strategy Agent completes in **< 30 min**: Lean Canvas + viability score + 3–5 ICPs + competitor analysis + bias audit.
- [ ] Product Planner Agent produces a PRD + feature list **after** the validation gate is approved.
- [ ] Founder Portal shows **live progress** and the **Validation Studio**; approve/pivot works from the UI.
- [ ] All agent I/O passes the guardrail pipeline (no raw user text reaches an LLM without PII/injection check).
- [ ] **Two orgs cannot see each other's data** (integration test).
- [ ] Cost per run tracked in `cost_ledger` and visible at `/v1/llmops/cost`.
- [ ] `ruff` + `mypy` + `pytest` + `eslint` + `tsc` all green in CI; security scan clean.
- [ ] **10 pilot clients** complete an idea→validated run successfully.

---

## 7. Phase Risks

| Risk | Mitigation |
|------|------------|
| Foundation is a single-person bottleneck (Asit) | Publish contracts day 1; delegate orchestrator (AF-033–035) or `BaseAgent` (AF-036) |
| Pillar 1 = 3 agents on one owner (Somesh) | Consider moving Research **or** Product Planner to a lighter owner |
| AF-046 Guardrails has no owner | Assign before any LLM call ships (Purnima/shared) |
| Gemini latency > 30-min SLA | Stream partial canvas; alert at 20 min; Redis result cache for repeated similar ideas |
| Tavily/SerpAPI rate limits | Backoff + 1 h Redis cache on tool results |

---

## 8. Current Status & Next Action

**Status**: Build Phase 1 (monorepo) ✅ done. Foundation: UDAL, FastAPI app, auth middleware, REST endpoints, migrations, Supabase Realtime, Redis integration, and the LangGraph orchestrator loop (AF-025–035) ✅ completed by Somesh.

**Next action (unblocks the most people):**
1. Asit: stand up Terraform networking + ECS + Supabase (AF-012–014), build **BaseAgent (AF-036)**.
2. Purnima: build Prompt Registry (AF-048), LiteLLM Router + RAG (AF-049), and Eval harness (AF-050).
3. Everyone else: start the offline work listed in `§5 Do-now-in-parallel` immediately — do not idle waiting on the foundation.

---

## Changelog

| Date | Version | Description |
|------|---------|-------------|
| 2026-06-06 | 1.1.0 | Mark AF-032 to AF-035 as completed and assigned to Somesh. |
| 2026-06-03 | 1.0.0 | Initial P1 (Validation Engine) phase plan — goal, scope, AF-task vertical slice, 6-week sprint plan, critical-path wiring, exit criteria, risks, next actions. Grounded in CLAUDE.md §45 + TASKS.md + task_assigned.md. |
