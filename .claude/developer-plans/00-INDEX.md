# AutoFounder AI — Implementation Plans Index

> **Index** · Updated: 2026-06-14
> **Sole Developer:** Kaushlendra Kumar Gupta
> All plans are now owned and executed by **Kaushlendra Kumar Gupta** as the sole developer on this project.

---

## The Plans

| # | File | Owner | Area | AF-IDs | Branch | Status |
|---|---|---|---|---|---|---|
| 01 | [01-asit-platform-foundation-plan.md](01-asit-platform-foundation-plan.md) | **Kaushlendra Kumar Gupta** | Platform Foundation (infra + UDAL + FastAPI + orchestrator + BaseAgent + Tool Registry) | AF-012 → AF-036, AF-047 | `feature/*` | ✅ Done |
| 02 | [02-somesh-pillar-1-strategy-research-plan.md](02-somesh-pillar-1-strategy-research-plan.md) | **Kaushlendra Kumar Gupta** | Pillar 1 — Strategy + Research + Product Planner | AF-037, AF-038, AF-039 | `feature/strategy-agent` | ✅ Done |
| 03 | [03-kaushlendra-pillar-2-architecture-plan.md](03-kaushlendra-pillar-2-architecture-plan.md) | **Kaushlendra Kumar Gupta** | Pillar 2 — Architect Agent | AF-040 | `kaushal-feat/agents/architect` | ❌ Pending |
| 04 | [04-kartik-pillar-3-codegen-plan.md](04-kartik-pillar-3-codegen-plan.md) | **Kaushlendra Kumar Gupta** | Pillar 3 — Coder Agent | AF-041 | `kaushal-feat/agents/coder` | ❌ Pending |
| 05 | [05-vishal-pillar-4-testing-plan.md](05-vishal-pillar-4-testing-plan.md) | **Kaushlendra Kumar Gupta** | Pillar 4 — Reviewer / Self-Healer | AF-042 | `feature/reviewer-agent` | ✅ Done |
| 06 | [06-prasenjit-pillar-5-deployment-plan.md](06-prasenjit-pillar-5-deployment-plan.md) | **Kaushlendra Kumar Gupta** | Pillar 5 — DevOps Agent | AF-043 | `kaushal-feat/agents/devops` | ❌ Pending |
| 07 | [07-pallavi-pillar-6-marketing-plan.md](07-pallavi-pillar-6-marketing-plan.md) | **Kaushlendra Kumar Gupta** | Pillar 6 — Marketing Agent | AF-044 | `kaushal-feat/agents/marketing` | ❌ Pending |
| 08 | [08-purnima-pillar-7-llmops-plan.md](08-purnima-pillar-7-llmops-plan.md) | **Kaushlendra Kumar Gupta** | Pillar 7 — LLMOps + shared Prompt Registry / Router / Eval | AF-045, AF-048, AF-049, AF-050 | `kaushal-feat/llmops/*` | ❌ Pending |
| 09 | [09-raunak-web-frontend-plan.md](09-raunak-web-frontend-plan.md) | **Kaushlendra Kumar Gupta** | Web — Next.js 14 Founder Portal (12 surfaces) | AF-051 → AF-062 | `kaushal-feat/frontend/*` | ❌ Pending |
| 10 | [10-yogesh-mobile-plan.md](10-yogesh-mobile-plan.md) | **Kaushlendra Kumar Gupta** | Mobile — Expo React Native (9 screens) | AF-063 → AF-071 | `kaushal-feat/mobile/*` | ❌ Pending |
| 11 | [11-asit-guardrails-pipeline-plan.md](11-asit-guardrails-pipeline-plan.md) | **Kaushlendra Kumar Gupta** | Guardrails & Governance — 6-stage pipeline wrapping every agent call | AF-046 | `feat/platform/guardrails-tool-registry` | ✅ Done |
| 12 | [12-asit-vscode-extension-plan.md](12-asit-vscode-extension-plan.md) | **Kaushlendra Kumar Gupta** | VS Code Extension — in-IDE co-founder (7 tasks) | AF-072 → AF-078 | `feature/vscode-extension` | ✅ Done |
| 13 | [13-asit-finance-ops-risk-plan.md](13-asit-finance-ops-risk-plan.md) | **Kaushlendra Kumar Gupta** | Finance Agent + Ops & Risk Agent (cross-cutting) | — (Phase 4) | `kaushal-feat/agents/finance` | ⏳ Phase 4 |

---

## Delivery Status

**✅ Done (49 tasks):** Plans 01, 02, 05, 11, 12 are fully delivered — platform foundation, all Pillar-1 agents (Strategy/Research/Product Planner), Reviewer agent, Guardrails, Tool Registry, VS Code Extension.

**❌ Pending (29 tasks):** Plans 03, 04, 06, 07, 08, 09, 10 — all to be built by Kaushlendra Kumar Gupta.

**Build Order** → see [`KAUSHLENDRA-SOLO-PLAN.md`](../KAUSHLENDRA-SOLO-PLAN.md) at the project root for the full prioritised sequence.

---

## Pillar Pipeline (Solo Flow)

```
Kaushlendra builds and owns the entire pipeline:

[DONE] Pillar 1: Strategy → Research → Product Planner → PRD + personas + canvas
         |
[NEXT]  Pillar 2: Architect Agent → ERD + OpenAPI + FEATURE LIST
         |
         v
        Pillar 3: Coder Agent → generated repo (FastAPI + Next.js)
         |
         v
[DONE] Pillar 4: Reviewer → tested green repo
         |
         v
        Pillar 5: DevOps Agent → live_url + deployed infra
        Pillar 6: Marketing Agent → launch package (uses FEATURE LIST from P2)
         |
         v
        Pillar 7: LLMOps Agent → cost tracking, prompt optimisation, drift monitoring

        Web Portal (12 surfaces) + Mobile App (9 screens) → consume all pillar outputs
```

---

## The One Dependency Rule

Every agent (Pillars 2–7) needs AF-048 (Prompt Registry) + AF-049 (LLM Router) before it can run end-to-end. Build those first, then tackle the pillar agents in pipeline order.

---

*AutoFounder AI · Developer Plans Index · Kaushlendra Kumar Gupta · 2026-06-14*
