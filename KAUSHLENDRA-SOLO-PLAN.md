# AutoFounder AI — Kaushlendra Kumar Gupta · Solo Development Plan

> **Owner:** Kaushlendra Kumar Gupta (sole developer)
> **Date:** 2026-06-14
> **Phase:** 1 — Validation Engine (continuing from team baseline)
> **Branch convention:** `kaushal-feat/<area>/<short-description>`

---

## What Is Already Done (Inherited Baseline)

| Area | Tasks | Status |
|------|-------|--------|
| Monorepo & Boilerplate | AF-001 → AF-011 | ✅ Complete |
| Infrastructure & Cloud (Terraform, ECS, Supabase, Redis, S3, CI/CD, OTel) | AF-012 → AF-024 | ✅ Complete (some follow-ups noted) |
| Core API & Data Layer (FastAPI, Alembic, UDAL, Auth, REST, Realtime) | AF-025 → AF-031 | ✅ Complete (AF-030 partial, AF-031 scaffold) |
| Orchestrator (Redis checkpointer, LangGraph StateGraph, HITL, SQS worker) | AF-032 → AF-035 | ✅ Complete |
| BaseAgent contract | AF-036 | ✅ Complete |
| Pillar 1 — Strategy + Research + Product Planner agents | AF-037, AF-038, AF-039 | ✅ Complete |
| Pillar 4 — Reviewer / Self-Healer agent | AF-042 | ✅ Complete |
| Guardrails 6-stage pipeline | AF-046 | ✅ Complete |
| Tool Registry | AF-047 | ✅ Complete |
| VS Code Extension (7 tasks) | AF-072 → AF-078 | ✅ Complete |

---

## What Remains — My Build Queue (29 Tasks)

### Priority 1 — Shared Infrastructure (Unblocks ALL Agents)

> These must land first. Every pillar agent's prompt resolution and model routing depends on them.

| ID | Task | Branch | Depends on | Est. |
|----|------|--------|------------|------|
| AF-048 | Prompt Registry — versioned Jinja2 templates in `prompt_registry` table + S3; `get()` resolves active/canary; deterministic canary split; strict variable validation | `kaushal-feat/llmops/prompt-registry` | AF-025 ✅ | ~5 hrs |
| AF-049 | LiteLLM Model Router + RAG — task-class → model routing (Gemini 3.5 Flash; gemini-embedding-2 768-dim); hybrid BM25 + ANN on Supabase pgvector; Cohere reranking; context compression; citation check | `kaushal-feat/llmops/model-router-rag` | AF-027 ✅, AF-014 ✅ | ~11 hrs |
| AF-050 | Eval harness — Promptfoo golden sets per agent, LangSmith batch eval runner, CI gate blocking prompt promotion on score regression > 2% | `kaushal-feat/llmops/eval-harness` | AF-048 | ~5 hrs |

### Priority 2 — Agent Pipeline (Pillars 2, 3, 5, 6)

> The agent chain: Architecture → Code → DevOps → Marketing. Each feeds the next.

| ID | Task | Branch | Depends on | Est. |
|----|------|--------|------------|------|
| AF-040 | Architect Agent (Pillar 2) — translates PRD into microservices HLD/LLD, ERD, OpenAPI contracts, DB models, and FEATURE LIST for Coder | `kaushal-feat/agents/architect` | AF-036 ✅, AF-039 ✅ | ~12 hrs |
| AF-041 | Coder Agent (Pillar 3) — generates production-ready FastAPI backend + Next.js frontend scaffolding from PRD + FEATURE LIST | `kaushal-feat/agents/coder` | AF-040 | ~14 hrs |
| AF-043 | DevOps Agent (Pillar 5) — writes Dockerfiles, GitHub Actions CI/CD, Terraform for cloud provisioning, DNS/SSL setup | `kaushal-feat/agents/devops` | AF-041 ✅, AF-042 ✅ | ~12 hrs |
| AF-044 | Marketing Agent (Pillar 6) — creates brand voice, SEO landing page, email drip campaign, social launch kit, Product Hunt kit | `kaushal-feat/agents/marketing` | AF-040 (FEATURE LIST) | ~10 hrs |

### Priority 3 — LLMOps Agent (Pillar 7)

> Runs last — needs live traces from all 7 pillars before it can optimise.

| ID | Task | Branch | Depends on | Est. |
|----|------|--------|------------|------|
| AF-045 | LLMOps Agent — trace analysis, DSPy prompt optimisation, Promptfoo regression gate, LiteLLM routing updates, TruLens drift monitoring, A/B experiments, FinOps report; weekly Step Functions cycle | `kaushal-feat/agents/llmops` | AF-036 ✅, AF-048, AF-049, AF-050, **all 7 pillars running** | ~16 hrs |

### Priority 4 — Web Frontend (Next.js 14 Founder Portal, 12 surfaces)

| ID | Task | Branch | Depends on | Est. |
|----|------|--------|------------|------|
| AF-051 | Next.js 14 project bootstrap — App Router, Tailwind v4, shadcn/ui, Supabase client, Zustand, React Query, `@autofounder-ai/api-client` wired | `kaushal-feat/frontend/bootstrap` | Phase 1 ✅ | ~3 hrs |
| AF-052 | Auth screens — `/login`, `/signup`, `/forgot-password` (Supabase Magic Link + Google OAuth) | `kaushal-feat/frontend/auth` | AF-051 | ~3 hrs |
| AF-053 | Founder Dashboard `/dashboard` — run cards, global status, idea input widget | `kaushal-feat/frontend/dashboard` | AF-051, AF-030 | ~4 hrs |
| AF-054 | Idea Submission flow `/ideas/new` — multi-step wizard, pillar progress stepper | `kaushal-feat/frontend/idea-submit` | AF-053 | ~3 hrs |
| AF-055 | Strategy & Research view `/runs/[id]/strategy` — Lean Canvas, SWOT, personas, viability score | `kaushal-feat/frontend/strategy-view` | AF-054 | ~4 hrs |
| AF-056 | Architecture view `/runs/[id]/architecture` — ERD diagram (Mermaid), OpenAPI viewer, stack card | `kaushal-feat/frontend/architecture-view` | AF-055 | ~4 hrs |
| AF-057 | Code Generation view `/runs/[id]/code` — file tree browser, syntax-highlighted code viewer, download ZIP | `kaushal-feat/frontend/code-view` | AF-056 | ~4 hrs |
| AF-058 | Testing & Review view `/runs/[id]/review` — test results panel, self-heal log, coverage badge | `kaushal-feat/frontend/review-view` | AF-057 | ~3 hrs |
| AF-059 | Deployment view `/runs/[id]/deploy` — live URL card, infra map, CI/CD logs stream (WebSocket) | `kaushal-feat/frontend/deploy-view` | AF-058 | ~4 hrs |
| AF-060 | Marketing view `/runs/[id]/marketing` — landing page preview, launch kit download, social scheduler | `kaushal-feat/frontend/marketing-view` | AF-059 | ~3 hrs |
| AF-061 | Billing & Settings `/settings` + `/billing` — Stripe subscription, usage meters, API key management | `kaushal-feat/frontend/billing` | AF-053 | ~4 hrs |
| AF-062 | Super-Admin portal `/admin` — tenant management, model cost dashboard, system health, run audit logs | `kaushal-feat/frontend/admin` | AF-061 | ~5 hrs |

### Priority 5 — Mobile App (Expo React Native, 9 screens)

| ID | Task | Branch | Depends on | Est. |
|----|------|--------|------------|------|
| AF-063 | Expo project bootstrap — TypeScript, Expo Router, NativeWind, Supabase client, push notifications | `kaushal-feat/mobile/bootstrap` | Phase 1 ✅ | ~3 hrs |
| AF-064 | Auth screens — Login / Sign-up / Magic Link (Supabase) | `kaushal-feat/mobile/auth` | AF-063 | ~2 hrs |
| AF-065 | Home / Dashboard screen — run list, global status cards | `kaushal-feat/mobile/dashboard` | AF-064 | ~3 hrs |
| AF-066 | New Idea screen — single-field capture, pillar progress bar | `kaushal-feat/mobile/new-idea` | AF-065 | ~2 hrs |
| AF-067 | Run Detail screen — pillar tab navigator (Strategy → LLMOps) | `kaushal-feat/mobile/run-detail` | AF-066 | ~4 hrs |
| AF-068 | HITL Approval screen — approve/reject lean canvas, PRD, deploy | `kaushal-feat/mobile/hitl` | AF-067 | ~3 hrs |
| AF-069 | Notifications screen — push notification history, action centre | `kaushal-feat/mobile/notifications` | AF-068 | ~2 hrs |
| AF-070 | Settings screen — profile, API key, subscription status | `kaushal-feat/mobile/settings` | AF-069 | ~2 hrs |
| AF-071 | Monitoring screen — live URL health, cost meter, LLMOps drift alerts | `kaushal-feat/mobile/monitoring` | AF-070 | ~3 hrs |

---

## Recommended Build Order (Strict Sequence)

```
[DONE] Foundation (AF-001–039, AF-042, AF-046–047, AF-072–078)
         |
         v
 [1] AF-048 Prompt Registry
         |
         v
 [2] AF-049 LLM Router + RAG
         |
    [3a] AF-050 Eval Harness
         |
    [3b] AF-040 Architect Agent   ← your original task; gates the whole build chain
         |
    [4]  AF-041 Coder Agent
         |
    [5a] AF-043 DevOps Agent
    [5b] AF-044 Marketing Agent   ← can start after AF-040 (uses FEATURE LIST)
         |
    [6]  AF-045 LLMOps Agent      ← needs traces from all 7 pillars live
         |
    [7]  AF-051–062 Frontend (Next.js 14 — 12 surfaces)
         |
    [8]  AF-063–071 Mobile (Expo — 9 screens)
```

---

## Daily Work Pattern (Suggested)

1. **Start each session:** `git pull origin main` + `make quality` to ensure green baseline.
2. **One task at a time** — complete, test (`make quality`), PR, merge before next.
3. **Branch naming:** `kaushal-feat/<area>/<task>` (e.g. `kaushal-feat/agents/architect`).
4. **Commit style:** Conventional Commits (`feat(architect): add ERD generation node`).
5. **No direct push to main** — always PR, even as solo developer (protects history).

---

## Key Shared Contracts (Don't Drift From These)

| Contract | Defined in | Used by |
|----------|-----------|---------|
| `ProductPlannerOutput` (PRD + requirements + user stories) | `backend/app/agents/product_planner/schema.py` | AF-040 Architect reads this |
| `ArchitectOutput` (HLD, LLD, ERD, OpenAPI, FEATURE LIST) | `backend/app/agents/architect/schema.py` ← **you define this** | AF-041 Coder reads this |
| `CoderOutput` (generated repo zip, file tree) | `backend/app/agents/coder/schema.py` | AF-042 Reviewer, AF-043 DevOps |
| `LLMRouterProtocol` | `backend/app/agents/_providers/` | every agent |
| `ToolRegistryProtocol` | `backend/app/agents/_providers/` | every tool-using agent |

---

*AutoFounder AI · Solo Plan · Kaushlendra Kumar Gupta · 2026-06-14*
