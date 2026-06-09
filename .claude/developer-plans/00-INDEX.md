# AutoFounder AI — Per-Developer Technical Implementation Plans

> **Index** · Date: 2026-06-04 · Phase 1 (Validation Engine)
> One technical implementation plan per developer, each mirroring the same 10-section + 3-appendix structure (modeled on Pallavi's Pillar 6 plan and grounded in `.claude/CLAUDE.md`, `.claude/task_assigned.md`, and each pillar's spec in `docs/architecture/Agents-Architecture/`).

---

## The Plans

| # | File | Developer | Area | AF-IDs | Branch |
|---|---|---|---|---|---|
| 01 | [01-asit-platform-foundation-plan.md](01-asit-platform-foundation-plan.md) | **Asit Piri** (Lead) | Platform Foundation (infra + UDAL + FastAPI + orchestrator + BaseAgent + Tool Registry) | AF-012 → AF-036, AF-047 | `feature/*` ✅ |
| 02 | [02-somesh-pillar-1-strategy-research-plan.md](02-somesh-pillar-1-strategy-research-plan.md) | **Somesh Chitranshi** | Pillar 1 — Strategy + Research + Product Planner | AF-037, AF-038, AF-039 | `feature/strategy-agent` |
| 03 | [03-kaushlendra-pillar-2-architecture-plan.md](03-kaushlendra-pillar-2-architecture-plan.md) | **Kaushlendra Kumar Gupta** | Pillar 2 — Architect Agent | AF-040 | `feature/architect-agent` |
| 04 | [04-kartik-pillar-3-codegen-plan.md](04-kartik-pillar-3-codegen-plan.md) | **Kartik Mogalapalli** | Pillar 3 — Coder Agent | AF-041 | `feature/coder-agent` |
| 05 | [05-vishal-pillar-4-testing-plan.md](05-vishal-pillar-4-testing-plan.md) | **Vishal Prasad** | Pillar 4 — Reviewer / Self-Healer | AF-042 | `feature/reviewer-agent` ✅ |
| 06 | [06-prasenjit-pillar-5-deployment-plan.md](06-prasenjit-pillar-5-deployment-plan.md) | **Prasenjit Roy** | Pillar 5 — DevOps Agent | AF-043 | `feature/devops-agent` |
| 07 | [07-pallavi-pillar-6-marketing-plan.md](07-pallavi-pillar-6-marketing-plan.md) | **Pallavi Anil Sindkar** | Pillar 6 — Marketing Agent | AF-044 | `feature/marketing-agent` |
| 08 | [08-purnima-pillar-7-llmops-plan.md](08-purnima-pillar-7-llmops-plan.md) | **Purnima** | Pillar 7 — LLMOps + shared Prompt Registry / Router / Eval | AF-045, AF-048, AF-049, AF-050 | `feature/llmops-agent` |
| 09 | [09-raunak-web-frontend-plan.md](09-raunak-web-frontend-plan.md) | **Raunak Ravi** | Web — Next.js 14 Founder Portal (12 surfaces) | AF-051 → AF-062 | `feature/nextjs-setup` |
| 10 | [10-yogesh-mobile-plan.md](10-yogesh-mobile-plan.md) | **Yogesh Raut** | Mobile — Expo React Native (9 screens) | AF-063 → AF-071 | `feature/expo-setup` |
| 11 | [11-asit-guardrails-pipeline-plan.md](11-asit-guardrails-pipeline-plan.md) | **Asit Piri** (Purnima co-owns Output+Monitoring) | Guardrails & Governance — 6-stage pipeline wrapping every agent call | AF-046 | `feat/platform/guardrails-tool-registry` ✅* |
| 12 | [12-asit-vscode-extension-plan.md](12-asit-vscode-extension-plan.md) | **Asit Piri** (delegate candidate: Raunak) | VS Code Extension — in-IDE co-founder (7 tasks) | AF-072 → AF-078 | `feature/vscode-extension-core` |
| 13 | [13-asit-finance-ops-risk-plan.md](13-asit-finance-ops-risk-plan.md) | **Asit Piri** (Phase 4, deferred) | Finance Agent + Ops & Risk Agent (cross-cutting) | — (Phase 4) | `feature/finance-agent` |

> **Previously unassigned — now all owned by Asit** (reassigned 2026-06-04, plans 11–13 above): Guardrails (AF-046), VS Code Extension (AF-072 → AF-078), Finance & Ops/Risk agents (Phase 4). ⚠️ This raises Asit to **~34 tasks (bus-factor 1)** — `task_assigned.md` Part B flags delegating the orchestrator (AF-033–035), BaseAgent (AF-036), or the VS Code Extension to an early-finishing pillar owner.
>
> **✅ Update 2026-06-09 (Vishal exec for Asit):** Plan **11 (AF-046 Guardrails)** + the **AF-047 Tool Registry** half of plan **01** are delivered on `feat/platform/guardrails-tool-registry` (off `dev`), verified green (ruff + mypy 210 files + 369 pytest, +127 new). With infra (AF-012–024), BaseAgent (AF-036), and the VS Code Extension (AF-072–078) already done, **Asit's only remaining work is plan 13 (Finance + Ops/Risk, Phase-4 deferred).**

---

## Pillar Hand-off Chain (who feeds whom)

```
Somesh (P1)          Kaushlendra (P2)      Kartik (P3)        Vishal (P4)       Prasenjit (P5)     Pallavi (P6)
idea -> canvas   ->  ERD + OpenAPI    ->   generated     ->  tested green  ->  live_url      ->   launch
+ personas + PRD     + FEATURE LIST        repo               repo             + deploy           package
                          |                                                        |
                          +----------------- FEATURE LIST -------------------------+--> Pallavi (P6)
                                            (hallucination ground truth)

ALL agents --> traces --> Purnima (P7 LLMOps) --> optimized prompts/models --> back into P1 / P3 / P6
Asit (Platform) --> UDAL + BaseAgent + REST + Realtime + orchestrator --> EVERY pillar + Raunak (Web) + Yogesh (Mobile)
```

## The One Rule That Explains Every Dependency

Every agent (Pillars 1–7) needs the **shared backend foundation** first — `UDAL` (AF-027), `BaseAgent` (AF-036), the LLM Router + Prompt Registry (AF-048/049), and the Orchestrator (AF-033). Until those land (Asit + Purnima), agent owners build everything *around* their agent offline — prompts, tools, schemas, evals, mocked tests — but cannot ship a *running* one. Frontend (Raunak) and Mobile (Yogesh) build every screen on **mock data** now and swap in the real API client when AF-030 REST + AF-031 Realtime land.

## What Each Plan Contains

Each `*-plan.md` follows the same skeleton:

1. **Objective** — what it achieves, outputs, inputs from upstream, outputs for downstream
2. **Dependencies** — mandatory + soft + fallback matrix + dependency chain
3. **Architecture** — design philosophy, main class/module, internal node/component diagram, responsibilities
4. **Workflow Design** — end-to-end flow, Mermaid sequence, data passed between nodes
5. **Sub-Agent / Sub-Component Recommendations** — node vs separate vs deferred
6. **Tools & Integrations** — per-node tools, LLM/library requirements, rate limits, DB/storage
7. **Data Models** — Pydantic / TypeScript schemas
8. **Development Roadmap** — Phase 1/2/3 week-by-week
9. **Testing Strategy** — mocks, fixtures, scenarios
10. **Deliverables** — file tree, env vars, registries, metrics, events, output contract, **Start-Today items**
- **Appendices** — A: Key Decisions · B: Risk Register · C: Coordination Checklist

---

*Auto-Founder AI — Developer Plans Index v1.0.0 | June 2026*
