# AutoFounder AI — Frontend Review Checklist

> **Purpose:** Obtain formal sign-off before Next.js implementation begins (AF-051 → AF-062).  
> **Owner:** Raunak Ravi  
> **Date:** June 2026  
> **Version:** 1.0

---

## How to use this document

1. Review the referenced artifacts (links below).
2. Walk the static prototype: open `prototype/index.html` in a browser and follow the happy path.
3. Discuss open items marked **⚠ Review** with the listed owner.
4. Check each box only when the reviewer agrees the item is **approved for implementation**.
5. Complete **§7 Final Sign-Off** before creating the Next.js app scaffold.

### Reference artifacts

| Artifact | Path |
|----------|------|
| Project understanding | `raunak-docs/project_understanding.md` |
| UX specification | `raunak-docs/frontend_ux_spec.md` |
| Frontend inventory | `raunak-docs/frontend_inventory.md` |
| API inventory | `raunak-docs/api_inventory.md` |
| Engineering gap analysis | `raunak-docs/engineering_gap_analysis.md` |
| Review package v1 | `docs/review_package_v1.md` |
| OpenAPI contract | `docs/openapi.yaml` |
| Static prototype | `prototype/*.html` |
| Agent mock data | `mock-data/` |
| Task ownership | `PROJECT-1-AutoFounder-AI/.claude/task_assigned.md` |

---

## 1. Product Review

**Reviewers:** Product lead (Asit) · Founders / stakeholders · Raunak  
**Evidence:** `project_understanding.md`, `frontend_ux_spec.md`, `prototype/`

### 1.1 User journey

| # | Question | Reference | Notes |
|---|----------|-----------|-------|
| 1.1.1 | Login → submit idea → track build → approve gates → launch is the intended flow | UX spec §2–3 | |
| 1.1.2 | Founder stays in control at validation, architecture, infra spend, and launch gates | `project_understanding.md` §4 | |
| 1.1.3 | Pillars 3–4 (build + test) are mostly observational for the founder | UX spec, prototype `code-review.html` | |
| 1.1.4 | LLMOps is org-wide monitoring, not per-build | `llmops-dashboard.html` | |

- [ ] **User journey is correct and approved**

**⚠ Review:** Phase 1 MVP may exit after validation + PRD (`PLAN_PHASE.md`) — confirm whether P1 studios (Architecture → Launch) are in scope for first Next.js sprint or a later phase.

### 1.2 Screens

| # | Screen | Route | Prototype | Phase | Status |
|---|--------|-------|-----------|-------|--------|
| 1.2.1 | Login | `/login` | `index.html` | P0 | In prototype |
| 1.2.2 | Auth callback | `/auth/callback` | — | P0 | Not in prototype |
| 1.2.3 | Portal layout shell | `(portal)/layout` | All portal pages | P0 | Implicit in prototype |
| 1.2.4 | Idea Intake | `/idea` | `idea-intake.html` | P0 | In prototype |
| 1.2.5 | Run List / Dashboard | `/runs` | `dashboard.html` | P0 | In prototype |
| 1.2.6 | Run Detail | `/runs/[id]` | `run-detail.html` | P0 | In prototype |
| 1.2.7 | Validation Studio | `/runs/[id]/validation` | `validation-studio.html` | P0 | In prototype |
| 1.2.8 | Architecture Studio | `/runs/[id]/architecture` | `architecture-studio.html` | P1 | In prototype |
| 1.2.9 | Code Review Studio | `/runs/[id]/review` | `code-review.html` | P1 | In prototype |
| 1.2.10 | Deploy Console | `/runs/[id]/deploy` | `deploy-console.html` | P1 | In prototype |
| 1.2.11 | Launch Control | `/runs/[id]/launch` | `launch-control.html` | P1 | In prototype |
| 1.2.12 | LLMOps Dashboard | `/llmops` | `llmops-dashboard.html` | P1 | In prototype |
| 1.2.13 | Admin Dashboard | `/admin` | — | P2 | **Missing from prototype** |
| 1.2.14 | Not found | `/not-found` | — | P0 | **Missing from prototype** |

- [ ] **Screen list is complete for agreed MVP phase**
- [ ] **P0 screens are sufficient to start implementation**
- [ ] **P1/P2 deferrals are explicitly accepted** (Admin, optional: auth callback page in prototype)

**⚠ Review:** Idea Intake inventory includes PDF upload and voice input — confirm MVP vs Phase 2 for file/voice on `/idea`.

### 1.3 Workflows

| # | Workflow | Gate kind | Studio | Approved in prototype? |
|---|----------|-----------|--------|----------------------|
| 1.3.1 | Submit idea → new run | — | Idea Intake | ✅ |
| 1.3.2 | Validate → approve / pivot | `validation_approve` | Validation Studio | ✅ |
| 1.3.3 | Architecture → approve / reject | `architecture_approve` | Architecture Studio | ✅ |
| 1.3.4 | Code build + review (read-only) | — | Code Review Studio | ✅ |
| 1.3.5 | Deploy → approve infra spend | `infra_spend_approve` | Deploy Console | ✅ |
| 1.3.6 | Launch → approve marketing | `launch_approve` | Launch Control | ✅ |
| 1.3.7 | Cancel build | — | Run Detail | Button shown; API partial |
| 1.3.8 | Feedback on drafts (RLHF) | — | Launch Control | 👍/👎 in prototype; API exists |
| 1.3.9 | Workspace selection | — | Idea Intake | **Not in prototype** (P1 API) |
| 1.3.10 | Super-admin tenant management | — | Admin | **Not in scope for v1** |

- [ ] **Core gate workflows are correct**
- [ ] **No required workflow is missing for agreed MVP phase**

### Section 1 — Product Review sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product / Program | | | |
| Stakeholder | | | |
| Frontend lead (Raunak) | | | |

- [ ] **§1 Product Review — APPROVED**

---

## 2. Frontend Review

**Reviewers:** Raunak · Design · Product  
**Evidence:** `frontend_ux_spec.md`, `frontend_inventory.md`, `prototype/`

### 2.1 Navigation

| # | Item | Spec location | Prototype |
|---|------|---------------|-----------|
| 2.1.1 | Primary nav: New idea, My builds, AI costs | UX spec §4 | Sidebar + mobile bottom nav |
| 2.1.2 | Per-build nav: Overview + pillars 1–5 | UX spec §4 | Sidebar when in run context |
| 2.1.3 | Locked studios until stage reached | UX spec §4 | `run-detail.html` greyed tabs |
| 2.1.4 | Gate banner in header → correct studio | UX spec §5 | Amber banner on dashboard + run detail |
| 2.1.5 | Breadcrumbs on studio pages | UX spec §5 | Present on studio pages |
| 2.1.6 | Route SSoT: `/runs/[id]/validation` not legacy paths | `frontend_inventory.md` | Matches prototype filenames |

- [ ] **Navigation structure approved**

**⚠ Review:** Confirm canonical routes vs any stale `.next` build artifacts under `frontend/` (see gap analysis R-8).

### 2.2 Layout

| # | Layout area | Components (inventory) | Prototype |
|---|-------------|------------------------|-----------|
| 2.2.1 | Sidebar (desktop) | `AppSidebar` | ✅ |
| 2.2.2 | Header | `TopBar`, `CostTicker`, `GateBanner`, `UserMenu` | Partial (no user menu dropdown) |
| 2.2.3 | Dashboard table layout | `RunTable`, filters | ✅ |
| 2.2.4 | Validation two-column + tabs | UX spec §7 | ✅ |
| 2.2.5 | Architecture diagram + cost card | UX spec §8 | ✅ |
| 2.2.6 | Code review summary + diff | UX spec §9 | ✅ |
| 2.2.7 | Deploy log + live URL | UX spec §10 | ✅ |
| 2.2.8 | Launch brand + preview + social | UX spec §11 | ✅ |
| 2.2.9 | LLMOps charts + tables | UX spec §12 | ✅ (CSS bar charts) |
| 2.2.10 | Dark mode default | Prototype + UX | ✅ slate/violet theme |

- [ ] **Layout approved for all in-scope screens**
- [ ] **Portal shell (sidebar + header) approved**

### 2.3 Component structure

| # | Module / component group | AF-ID | Implement in Next.js? |
|---|--------------------------|-------|----------------------|
| 2.3.1 | Design system (`components/ui/*` shadcn) | AF-051 | Prerequisite |
| 2.3.2 | `lib/api-client.ts` + envelope parser | AF-052 | Yes |
| 2.3.3 | `useRun`, `useGate`, `useCost` hooks | AF-052 | Yes |
| 2.3.4 | Zustand + React Query stores | AF-053 | Yes |
| 2.3.5 | `Skeleton`, `EmptyState`, `ErrorState` | AF-051 | Yes |
| 2.3.6 | Studio-specific viewers (Mermaid, Monaco, iframe) | AF-055–059 | Per screen |
| 2.3.7 | `ErrorBoundary`, `Toaster` | AF-051 | Yes |

- [ ] **Shared component modules approved**
- [ ] **Per-screen component list in `frontend_inventory.md` approved**

### 2.4 Mobile behavior

| # | Behavior | UX spec | Prototype |
|---|----------|---------|-----------|
| 2.4.1 | Sidebar → bottom nav on small screens | §4, per-screen | ✅ bottom nav |
| 2.4.2 | Dashboard table → card list | §6 | Partial (table scroll) |
| 2.4.3 | Gate actions sticky footer on studios | §7–11 | Not fully implemented |
| 2.4.4 | Diff viewer → GitHub link fallback | §9 | ✅ in code-review |
| 2.4.5 | Touch targets ≥ 44px | § Global rules | ⚠ Review on implementation |

- [ ] **Mobile behavior approved** (prototype demonstrates intent; polish deferred to implementation)

### Section 2 — Frontend Review sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Frontend lead (Raunak) | | | |
| Design | | | |
| Product | | | |

- [ ] **§2 Frontend Review — APPROVED**

---

## 3. Backend Review

**Reviewers:** Somesh (API) · Asit (platform) · Raunak (consumer)  
**Evidence:** `docs/openapi.yaml`, `api_inventory.md`, `review_package_v1.md` §6

### 3.1 API endpoints

| # | Endpoint | Required for P0 UI | Contract | Backend today |
|---|----------|-------------------|----------|---------------|
| 3.1.1 | `GET /health` | Optional | ✅ | ✅ |
| 3.1.2 | `POST /v1/ideas` | Yes | ✅ | 🟡 Partial |
| 3.1.3 | `GET /v1/runs` | Yes | ✅ | 🟡 Partial |
| 3.1.4 | `GET /v1/runs/{id}` | Yes | ✅ | 🟡 Partial |
| 3.1.5 | `DELETE /v1/runs/{id}` | Yes | ✅ | 🟡 Partial |
| 3.1.6 | `GET /v1/runs/{id}/artifacts` | Yes | ✅ | 🟡 Partial |
| 3.1.7 | `POST /v1/runs/{id}/gates/{id}` | Yes | ✅ | 🟡 Partial |
| 3.1.8 | `GET /v1/runs/{id}/stream` | Yes (degrade OK) | ✅ planned | ❌ Missing |
| 3.1.9 | `GET /v1/llmops/cost` | Yes (layout) | ✅ | 🟡 Partial |
| 3.1.10 | `POST /v1/feedback` | P1 Launch | ✅ | 🟡 Partial |
| 3.1.11 | `GET /v1/llmops/cost/detail` | P1 LLMOps | ✅ planned | ❌ Missing |
| 3.1.12 | Workspaces CRUD | P1 | ✅ planned | ❌ Missing |
| 3.1.13 | Admin APIs | P2 | ✅ planned | ❌ Missing |

- [ ] **P0 endpoint set approved** (`openapi.yaml` as contract)
- [ ] **Known backend gaps accepted for mock-first implementation** (MSW until Somesh wires P0 blockers)
- [ ] **P1/P2 endpoints explicitly deferred**

**⚠ Review:** Frontend may start on mocks while F-052, F-067, F-040, F-059 are in progress — confirm timeline with Somesh.

### 3.2 Response schemas

| # | Schema | Frontend depends on | Contract complete? | Backend aligned? |
|---|--------|---------------------|--------------------|------------------|
| 3.2.1 | `RunRead` | All run screens | ✅ target fields | ❌ 4 fields only today |
| 3.2.2 | `GateRead` | Studios + layout banner | ✅ | 🟡 |
| 3.2.3 | `ArtifactRead` | All studios | ✅ | 🟡 |
| 3.2.4 | `ArtifactKind` enum | Artifact filtering | ✅ 17 kinds | 🟡 |
| 3.2.5 | `ArtifactMeta*` per kind | Studio renderers | Partial (8 of 17) | ❌ |
| 3.2.6 | `CostRead` | Layout + LLMOps | ✅ | 🟡 |
| 3.2.7 | `StreamEvent` | Run detail, deploy, review | ✅ | ❌ WS not live |
| 3.2.8 | `ErrorEnvelope` | All screens | ✅ | ✅ pattern exists |
| 3.2.9 | `PaginationInfo` | Dashboard | ✅ | 🟡 |

- [ ] **Response envelope pattern approved** (`{ data, meta }` / `{ error, meta }`)
- [ ] **`RunRead` target schema approved** (see `openapi.yaml`)
- [ ] **`ArtifactRead` + `kind` filter pattern approved**
- [ ] **Incomplete `ArtifactMeta*` schemas accepted with completion plan** (owner: Somesh + agent leads)

### 3.3 Error handling

| # | Case | HTTP | `error.code` | UI behavior (UX spec) |
|---|------|------|--------------|------------------------|
| 3.3.1 | Validation | 400 | `AF_ERR_VALIDATION` | Inline field errors |
| 3.3.2 | Unauthorized | 401 | `AF_ERR_UNAUTHORIZED` | Redirect to `/login` |
| 3.3.3 | Forbidden | 403 | `AF_ERR_FORBIDDEN` | Banner + message |
| 3.3.4 | Not found | 404 | `AF_ERR_NOT_FOUND` | Error state + back link |
| 3.3.5 | Cost cap | 402 | `AF_ERR_COST_CAP_EXCEEDED` | Top banner on Idea Intake |
| 3.3.6 | Gate conflict | 409 | `AF_ERR_GATE_ALREADY_DECIDED` | Inline on approve button |
| 3.3.7 | Rate limit | 429 | `AF_ERR_RATE_LIMITED` | Banner + `Retry-After` |
| 3.3.8 | Server error | 500 | `AF_ERR_INTERNAL` | Generic error state |

- [ ] **Error code mapping approved for UI**
- [ ] **No stack traces / internal paths in user-facing errors** (api-design rule)

### Section 3 — Backend Review sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| API / Backend (Somesh) | | | |
| Platform (Asit) | | | |
| Frontend consumer (Raunak) | | | |

- [ ] **§3 Backend Review — APPROVED**

---

## 4. Agent Review

**Reviewers:** Pillar agent owners · Somesh (orchestrator) · Raunak  
**Evidence:** `review_package_v1.md` §7–8, `mock-data/`, agent `schema.py` files

**Principle:** Production UI reads **artifacts via API only**. Agent outputs below are backend producer contracts.

### 4.1 Agent outputs

| Pillar | Agent | Output schema in code | Mock data | Orchestrator wired |
|--------|-------|----------------------|-----------|-------------------|
| 1 | Research | ✅ `ResearchOutput` | — | ❌ |
| 1 | Strategy | ✅ `StrategyOutput` | ✅ `mock-data/strategist/` | 🟡 |
| 1 | Product Planner | ✅ `ProductPlannerOutput` | — | ❌ post-gate |
| 2 | Architect | ❌ **Undefined** | ✅ `mock-data/architect/` | Stub |
| 3 | Coder | ❌ **Undefined** | ✅ `mock-data/coder/` | Stub |
| 4 | Reviewer | ✅ `ReviewerOutput` | ✅ `mock-data/reviewer/` | Stub |
| 5 | DevOps | 🟡 `DevOpsState` only | ✅ `mock-data/devops/` | Stub |
| 6 | Marketing | ❌ **Undefined** | ✅ `mock-data/marketing/` | Stub |
| 7 | LLMOps | ❌ **Undefined** | ✅ `mock-data/llmops/` | Not built |

- [ ] **Agent → artifact mapping approved** (review package §8 diagram)
- [ ] **Undefined agent schemas have owners and target dates before P1 UI depends on live data**
- [ ] **Mock-first UI does not import agent JSON in production code** (fixtures only)

### 4.2 Artifact formats

| `kind` | Studio | `ArtifactMeta` in OpenAPI | Approved for UI design? |
|--------|--------|---------------------------|-------------------------|
| `lean_canvas` | Validation | ✅ | |
| `market_report` | Validation | ❌ TBD | |
| `viability` | Validation | ✅ | |
| `prd` | Validation | ❌ TBD | |
| `erd` | Architecture | ✅ | |
| `openapi` | Architecture | ❌ TBD | |
| `stack` | Architecture | ❌ TBD | |
| `cost_forecast` | Architecture | Partial | |
| `review_report` | Code Review | ✅ | |
| `repo_url` | Code Review | ❌ TBD | |
| `deploy_url` | Deploy | ✅ | |
| `smoke_test` | Deploy | Partial | |
| `brand_kit` | Launch | ✅ | |
| `landing_page` | Launch | ✅ | |
| `social_posts` | Launch | ✅ | |
| `email_sequences` | Launch | ❌ TBD | |
| `blog_drafts` | Launch | ❌ TBD | |

- [ ] **Artifact `kind` enum approved** (stable; changes require OpenAPI bump)
- [ ] **`meta` vs `uri` payload strategy approved** (hybrid: inline `meta` + S3 `uri` for large blobs)
- [ ] **Missing `ArtifactMeta` schemas tracked as pre-P1 backend tasks**

### 4.3 Gate workflows

| Gate | Trigger | Founder actions | API | Resume pipeline on approve? |
|------|---------|-----------------|-----|---------------------------|
| `validation_approve` | After Pillar 1 research/strategy | Approve, Pivot (reject + notes) | `POST …/gates/{id}` | Yes → Architecture |
| `architecture_approve` | After Pillar 2 design | Approve, Reject | `POST …/gates/{id}` | Yes → Build |
| `infra_spend_approve` | Before cloud spend | Approve spend | `POST …/gates/{id}` | Yes → Deploy complete |
| `launch_approve` | Before publish | Approve, Edit, Reject | `POST …/gates/{id}` | Yes → Launch |
| `canary_rollout` | LLMOps (future) | — | Planned | — |

- [ ] **Gate kinds and states approved** (`pending` → `approved` | `rejected` | `timed_out`)
- [ ] **Gate decisions via REST only** (not WebSocket) approved
- [ ] **Pivot = `rejected` + notes** approved (no separate enum)

### Section 4 — Agent Review sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Orchestrator (Somesh) | | | |
| Pillar 1 (Nishant / team) | | | |
| Pillar 2–7 owners | | | |
| Frontend (Raunak) | | | |

- [ ] **§4 Agent Review — APPROVED**

---

## 5. Data Review

**Reviewers:** Raunak · Somesh · Agent owners  
**Evidence:** `mock-data/`, `frontend_inventory.md` § Mock fixture catalog, `prototype/` (PawTrail scenario)

### 5.1 Mock data

| # | Dataset | Location | Purpose | API-shaped? |
|---|---------|----------|---------|-------------|
| 5.1.1 | PawTrail strategist output | `mock-data/strategist/` | Validation content reference | ❌ agent-level |
| 5.1.2 | PawTrail architect output | `mock-data/architect/` | Architecture studio | ❌ agent-level |
| 5.1.3 | PawTrail coder output | `mock-data/coder/` | Code review context | ❌ agent-level |
| 5.1.4 | PawTrail reviewer output | `mock-data/reviewer/` | Code review studio | ❌ agent-level |
| 5.1.5 | PawTrail devops output | `mock-data/devops/` | Deploy console | ❌ agent-level |
| 5.1.6 | PawTrail marketing output | `mock-data/marketing/` | Launch control | ❌ agent-level |
| 5.1.7 | PawTrail LLMOps cycle | `mock-data/llmops/` | LLMOps dashboard | ❌ agent-level |
| 5.1.8 | Frontend API fixtures (MSW) | `frontend/tests/fixtures/` | P0 development | ❌ **Not created** |
| 5.1.9 | Static prototype copy | `prototype/*.html` | Stakeholder demo | N/A |

- [ ] **PawTrail as canonical demo narrative approved**
- [ ] **Agent mock data approved for backend/dev reference**
- [ ] **Plan to derive API-shaped fixtures (`ArtifactRead`, `RunRead`) for MSW approved** (F-136, first Next.js sprint task)

### 5.2 JSON schemas

| # | Schema | Location | Status |
|---|--------|----------|--------|
| 5.2.1 | OpenAPI 3.1 (API SSoT) | `docs/openapi.yaml` | ✅ v1.0 |
| 5.2.2 | Agent output schemas (7) | `mock-data/*/schema.json` | ✅ Draft 2020-12 |
| 5.2.3 | Generated TypeScript from OpenAPI | `frontend/src/lib/api/types.ts` | ❌ Not generated |
| 5.2.4 | Shared package types | `packages/shared` | ❌ Scaffold only |

- [ ] **`docs/openapi.yaml` approved as frontend type source** (`openapi-typescript` or equivalent)
- [ ] **Agent `mock-data/*/schema.json` approved as backend fixture reference only**
- [ ] **No production import of `mock-data/` agent schemas in Next.js app**

### Section 5 — Data Review sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Frontend (Raunak) | | | |
| Backend (Somesh) | | | |
| Agent owners | | | |

- [ ] **§5 Data Review — APPROVED**

---

## 6. Architecture Review

**Reviewers:** Asit · Somesh · Raunak  
**Evidence:** `api-design.md`, `openapi.yaml`, `frontend_ux_spec.md`, gap analysis

### 6.1 Realtime requirements

| # | Requirement | Spec | Backend | Frontend plan |
|---|-------------|------|---------|---------------|
| 6.1.1 | Live step log on Run Detail | `GET /v1/runs/{id}/stream` WS | ❌ Not implemented | `useRun` + stream hook (AF-052) |
| 6.1.2 | Event types | `step.started`, `token`, `gate.required`, `run.completed`, `run.failed` | Planned | Match `StreamEvent` in OpenAPI |
| 6.1.3 | Reconnect + replay | `Last-Event-ID` header, 30 min window | Planned | Hook must support |
| 6.1.4 | Gate decisions | REST only, not WS | ✅ | `POST …/gates/{id}` |
| 6.1.5 | Degraded mode | Poll `GET /v1/runs/{id}` if WS unavailable | — | Required for MVP |

- [ ] **WebSocket as primary realtime transport approved**
- [ ] **Polling fallback when stream unavailable approved**
- [ ] **Stream uses `step_key` + `pillar`, not agent class names** (OpenAPI contract)

**⚠ Review:** Open question OQ-2 — WebSocket vs Supabase Realtime; pick one before implementing `useRun` stream.

### 6.2 Authentication flow

| # | Step | Technology | Notes |
|---|------|------------|-------|
| 6.2.1 | Login | Supabase Auth (`@supabase/ssr`) | Google, GitHub, email |
| 6.2.2 | Callback | `/auth/callback` route | SSR session cookies |
| 6.2.3 | API calls | `Authorization: Bearer <JWT>` | Short-lived; silent refresh |
| 6.2.4 | JWT claims | `sub`, `organization_id`, `role`, `scope` | Tenant from token, never body |
| 6.2.5 | MFA | Supabase enforced | `MFAChallenge` component |
| 6.2.6 | Route protection | Next.js middleware | Redirect unauthenticated → `/login` |
| 6.2.7 | Admin routes | `role = super_admin` | `/admin` P2 |

- [ ] **Supabase Auth as sole human auth provider approved**
- [ ] **JWT → API client attachment pattern approved**
- [ ] **Middleware route groups approved:** public (`/login`, `/auth/callback`) vs portal (`(portal)/*`)

### Section 6 — Architecture Review sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Platform (Asit) | | | |
| Backend (Somesh) | | | |
| Frontend (Raunak) | | | |

- [ ] **§6 Architecture Review — APPROVED**

---

## 7. Final Sign-Off

### 7.1 Pre-implementation gates

All must be checked before `AF-051` (Next.js scaffold) starts:

| # | Gate | Owner | Done? |
|---|------|-------|-------|
| G-1 | §1 Product Review approved | Product | ☐ |
| G-2 | §2 Frontend Review approved | Raunak + Design | ☐ |
| G-3 | §3 Backend Review approved (contract; mocks OK for gaps) | Somesh + Raunak | ☐ |
| G-4 | §4 Agent Review approved (mapping + deferrals explicit) | Agent leads | ☐ |
| G-5 | §5 Data Review approved | Raunak | ☐ |
| G-6 | §6 Architecture Review approved | Asit + Somesh | ☐ |
| G-7 | Stakeholders walked `prototype/index.html` | All | ☐ |
| G-8 | Open questions in `review_package_v1.md` §10 resolved or accepted | Engineering leads | ☐ |

### 7.2 Implementation authorization

By signing below, reviewers confirm:

1. The Founder Portal scope, routes, and UX in this checklist match product intent.  
2. `docs/openapi.yaml` is the API contract; the UI will not depend on agent implementation types.  
3. Known backend gaps will not block **mock-first** Next.js work (MSW + fixtures).  
4. Live API integration proceeds only after P0 backend items F-040, F-052, F-067 are addressed (or per agreed timeline).  

| Section | Approved? | Reviewer | Date |
|---------|-----------|----------|------|
| §1 Product Review | ☐ Yes ☐ No | | |
| §2 Frontend Review | ☐ Yes ☐ No | | |
| §3 Backend Review | ☐ Yes ☐ No | | |
| §4 Agent Review | ☐ Yes ☐ No | | |
| §5 Data Review | ☐ Yes ☐ No | | |
| §6 Architecture Review | ☐ Yes ☐ No | | |

### 7.3 Final decision

- [ ] **APPROVED — Begin Next.js implementation (AF-051)**
- [ ] **APPROVED WITH CONDITIONS** — List conditions below
- [ ] **NOT APPROVED** — Block implementation until resolved

**Conditions / blockers (if any):**

```
(Write here)
```

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Program / Product lead** | | | |
| **Frontend lead (Raunak)** | | | |
| **API / Backend lead (Somesh)** | | | |
| **Platform lead (Asit)** | | | |

---

## Appendix — P0 implementation order (post sign-off)

Recommended first sprint after approval (from gap analysis + UX spec):

1. AF-051 — Next.js 14 + Tailwind + shadcn + Supabase Auth  
2. AF-135 — Design system primitives  
3. F-136 — API-shaped mock fixtures + MSW  
4. AF-052 / AF-053 — API client, hooks, layout shell  
5. AF-054, AF-061, AF-055 — Idea Intake, Dashboard, Validation Studio  
6. AF-137 — Playwright e2e (idea → gate) on mocks  

P1 studios (AF-056 → AF-060) follow after P0 exit criteria or in parallel on mocks.

---

*Frontend Review Checklist v1.0 — June 2026 · Companion to `docs/review_package_v1.md`*
