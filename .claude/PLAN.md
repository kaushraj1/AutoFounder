# AutoFounder AI — Master Plan

> **AutoFounder AI** converts a single text idea into a validated, built, deployed, and marketed software business autonomously — cutting the traditional 4–7 month, $20–60K founder journey down to **~7 days at < ₹500 COGS** per MVP.
>
> **This file** = the strategic master plan: the *vision*, the *roadmap*, the *milestones*, and the *order of build*. It ties together the other planning docs (see [Document Map](#document-map)). For granular task status use `.claude/TASKS.md`; for who-owns-what use `.claude/task_assigned.md`; for the active phase's execution detail use `.claude/PLAN_PHASE.md`.
>
> **Date**: 2026-06-03 · **Active product phase**: Phase 1 — Validation Engine · **Canonical authority**: `.claude/CLAUDE.md` overrides everything if any doc conflicts.

---

## 1. Document Map (how the planning docs fit together)

| Doc | Scope | Use it for |
|-----|-------|------------|
| `.claude/CLAUDE.md` | Architecture reference (10 layers, agents, guardrails, SLAs) | The "how it's built" source of truth |
| **`.claude/PLAN.md`** ← you are here | Strategic master plan | Vision, roadmap, milestones, build order |
| `.claude/PLAN_PHASE.md` | Active phase deep-dive | Executing the **current** phase, sprint by sprint |
| `.claude/TASKS.md` | 78-task tracker (AF-001…AF-078) | Per-task status & dependencies |
| `.claude/task_assigned.md` | Per-person ownership + independence + gaps | Who builds what, what's blocked |
| `.claude/PLAN-BUILD-SEQUENCE.md` | From-scratch build sequence (S0–S4, file order) | The granular engineering bring-up of the platform |
| `.claude/MEMORY.md` | Quick-reference (stack, dirs, commands, branches) | Fast onboarding / day-to-day lookups |
| `.claude/SKILL.md` | Dev skill (conventions + checklists) | Rules to follow while coding |

---

## 2. North Star

> **"A true AI co-founder that gets things done."**

| Dimension | Goal |
|-----------|------|
| Speed | Idea → validated in **< 30 min**; idea → live MVP in **~7 days** |
| Cost | **99% cheaper** — COGS per MVP **< ₹500** |
| Quality | Production-grade output: ≥ 80% test coverage, ≥ 85% first-run deploy success, OWASP-clean |
| Trust | Human-in-the-loop gates at every irreversible step; truthful marketing (feature-claim cross-check) |
| Scale | Multi-tenant from day 0 (schema-per-tenant + RLS); 500 concurrent builds target |

**Revenue target**: ₹50 Lakhs MRR within 12 months.

---

## 3. The Product — 7-Pillar Autonomous Pipeline

Every pillar is one specialized agent running the loop **Understand → Plan → Execute → Verify → Learn**.

| Pillar | Agent | Delivers | HITL Gate |
|--------|-------|----------|:---------:|
| 1 | Strategy & Ideation (+ Research, + Product Planner) | Lean Canvas, viability 0–100, ICPs, competitor analysis, PRD | ✅ Approve / Pivot |
| 2 | Architect | ERD, OpenAPI contract, stack selection, cost forecast | ✅ Approve |
| 3 | Coder | Full-stack Next.js 14 + FastAPI, auth, payments | — |
| 4 | Reviewer / Self-Healer | Tests, security scans, self-heal (≤ 5 cycles) | — (auto, escalate on fail) |
| 5 | DevOps | Containerize, Terraform, ECS, DNS/SSL, deploy | ✅ Infra-spend approval |
| 6 | Marketing | Brand kit, landing page, SEO, social launch | ✅ Launch Control Center |
| 7 | LLMOps | Telemetry, prompt-opt, model routing, drift, A/B | Auto if metrics pass |

---

## 4. Two Phasings (do not confuse them)

There are **two independent ways** the work is phased. Keeping them distinct avoids planning confusion.

### 4a. Product Phases — business rollout (from CLAUDE.md §45)

| Phase | Status | Scope | Milestone |
|-------|--------|-------|-----------|
| **P1 — Validation Engine** | **🟢 Active** | Strategy + Research + Product Planner agents; Lean Canvas; viability scoring | **10 pilot clients** |
| P2 — MVP Builder | Upcoming | Architect → Coder → Reviewer agents; ephemeral sandbox | 50 clients |
| P3 — Launch & GTM | Planned | Marketing agent; social integrations; Launch Control Center | 150 clients |
| P4 — Enterprise Scale | Planned | LLMOps CT pipelines; full AWS deploy automation; Finance & Ops/Risk agents | 300 clients |
| P5 — Global Expansion | Planned | Multi-region, localization, marketplace | 1,000 clients |

### 4b. Build Phases — engineering tracks (from `.claude/TASKS.md`)

| Build Phase | Tasks | Status | Owner(s) |
|-------------|-------|--------|----------|
| 1 — Monorepo & Boilerplate | AF-001 → AF-011 | ✅ Done (11/11) | Team |
| 2 — Infrastructure & Cloud | AF-012 → AF-024 | ❌ Pending | Asit |
| 3 — Backend (FastAPI + Agents) | AF-025 → AF-050 | ❌ Pending | Asit (3a/3b) · Pillar owners (3c) · Purnima (3d) |
| 4 — Frontend (Next.js 14) | AF-051 → AF-062 | ❌ Pending | Raunak |
| 5 — Mobile (Expo) | AF-063 → AF-071 | ❌ Pending | Yogesh |
| 6 — VS Code Extension | AF-072 → AF-078 | ❌ Pending (⚪ no owner) | — |

**The link between them:** Product **P1 (Validation Engine)** is delivered by completing Build Phases **2 + 3a/3b + the Pillar-1 slice of 3c/3d + the validation slice of Phase 4**. You do not need all build phases to ship P1 — only the vertical slice that makes idea→Lean Canvas→PRD work end to end. The detail lives in `.claude/PLAN_PHASE.md`.

---

## 5. Build Sequence Principles (locked)

1. **Bottom-up**: infra/data → core platform → agents → UI. Never build UI for an agent that doesn't exist.
2. **Vertical slices**: ship one complete slice (migration → UDAL → route → hook → component) — no half-open layers.
3. **UDAL mandatory**: agents never touch the DB directly — always through `AUTOFOUNDER-BACKEND/app/db` UDAL with a resolved `organization_id`.
4. **Tenant isolation from row 0**: schema-per-tenant + RLS before the first tenant row is written.
5. **Every agent call is wrapped** by the 6-stage guardrails pipeline (even a minimal version) before shipping.
6. **Working software over docs**: every sprint ends with something runnable.
7. **No hard-coded secrets/values**: Secrets Manager + SSM; enforced by `semgrep`.

> The dependency engine: nothing agent-related runs until the **foundation** lands — `UDAL` (AF-027) → `BaseAgent` (AF-036) → FastAPI (AF-028) → REST contracts (AF-030) → Prompt Registry + LLM Router (AF-048/049). These are the team's critical path.

---

## 6. Milestones & Definition of Done

| Milestone | Definition of Done | Target Phase |
|-----------|--------------------|:------------:|
| **M0 — Platform alive** | `POST /v1/ideas` returns `run_id` < 500 ms; health checks green; one tenant isolated | Build P2 + P3a |
| **M1 — Validation Engine** | Idea → Lean Canvas + viability score + 3 ICPs in < 30 min; PRD after gate approval; Validation Studio UI live; 10 pilot clients running | Product **P1** |
| **M2 — MVP Builder** | Architect → Coder → Reviewer produce a tested, deployable repo in a sandbox | Product P2 |
| **M3 — Launch & GTM** | Marketing agent produces brand + landing + social, gated by Launch Control Center | Product P3 |
| **M4 — Enterprise Scale** | LLMOps continuous-learning loop live; one-click AWS deploy; per-tenant FinOps | Product P4 |
| **M5 — Global** | Multi-region, localization, agent/template marketplace | Product P5 |

**Phase-1 (M1) exit criteria** (the bar for "Validation Engine done"): see `.claude/PLAN_PHASE.md § Exit Criteria`.

---

## 7. Current Status Snapshot

| Area | State |
|------|-------|
| Build Phase 1 (Monorepo) | ✅ Complete (AF-001 → AF-011) |
| Build Phase 2 (Infra) | ❌ Not started — **critical path, owner Asit** |
| Foundation (UDAL, BaseAgent, FastAPI, orchestrator) | ❌ Not started — blocks all agents |
| Pillar-1 agents (Strategy / Research / Product Planner) | 🟡 Offline prep only (prompts, schemas, tools) until foundation lands |
| Frontend / Mobile | 🟡 Design on mock data can start now (Raunak / Yogesh) |
| Supabase | Connected (project linked); migrations not yet applied |
| Kafka | Confluent Cloud provisioned |
| Open gaps | VS Code Extension unowned; Guardrails (AF-046) unowned; Pillar-1 overloaded (3 agents on one owner) — see `task_assigned.md § Part D` |

---

## 8. Top Risks (master view)

| Risk | Mitigation | Detail |
|------|------------|--------|
| Foundation bottleneck (1 person gates 9) | Delegate orchestrator / BaseAgent; publish I/O contracts day 1 | `task_assigned.md §D-B` |
| LLM hallucination in generated code/marketing | Output guardrail + LLM-as-judge + feature-list cross-ref + ≥80% coverage | CLAUDE.md §47 |
| Prompt injection via idea text | Input guardrail (Llama Guard + injection classifier + PII redaction) | CLAUDE.md §34 |
| Tenant data leakage | UDAL tenant-scoping + schema-per-tenant + RLS + per-tenant vector namespaces | CLAUDE.md §39 |
| Runaway LLM cost | Per-tenant caps, circuit breakers, cheapest-capable router, semantic cache | CLAUDE.md §38 |
| Unowned scope (VS Code, Guardrails) | Assign owners before those phases start | `task_assigned.md §D` |

---

## 9. Cross-Reference Index

- **Architecture / SLAs / agents** → `.claude/CLAUDE.md`
- **Active phase execution** → `.claude/PLAN_PHASE.md`
- **Task status (AF-IDs)** → `.claude/TASKS.md`
- **Ownership / dependencies / gaps** → `.claude/task_assigned.md`
- **Granular bring-up (file order, sprints S0–S4)** → `.claude/PLAN-BUILD-SEQUENCE.md`
- **Stack / commands / branches** → `.claude/MEMORY.md`
- **Coding conventions / checklists** → `.claude/SKILL.md`

---

## Changelog

| Date | Version | Description |
|------|---------|-------------|
| 2026-06-03 | 1.0.0 | Initial master plan — vision, 7-pillar product, two-phasing model (product vs build), milestones + DoD, build principles, status snapshot, risk + cross-reference index. Grounded in CLAUDE.md + README (PRD). |
