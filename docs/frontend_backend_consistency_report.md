# AutoFounder AI — Frontend / Backend Consistency Report

> **Purpose:** Compare static prototype, frontend inventory, API inventory, and live backend implementation.  
> **Date:** June 2026  
> **Version:** 1.0  
> **Sources:** `prototype/`, `raunak-docs/frontend_inventory.md`, `raunak-docs/api_inventory.md`, `docs/openapi.yaml`, `PROJECT-1-AutoFounder-AI/backend/app/api/v1/*`

---

## Executive summary

| Layer | Alignment | Notes |
|-------|-----------|-------|
| **Prototype ↔ UX inventory** | High | 10/14 inventoried screens have HTML prototypes; routes match `frontend_inventory.md` |
| **API inventory ↔ OpenAPI** | High | `docs/openapi.yaml` matches `api_inventory.md` target contract |
| **Backend ↔ OpenAPI** | Low | `RunRead` exposes 4 fields vs 12+ in contract; several endpoints missing or partial |
| **Backend ↔ Prototype data needs** | Low | No live artifacts, gates on runs, stream, or orchestrator kickoff for idea submit |
| **WebSocket** | None | No `/v1/runs/{id}/stream` route in backend |

**P0 blockers for live API integration:** ORM/tenant schema alignment, `POST /v1/ideas` → orchestrator + `idea_text` persistence, expanded `RunRead` + embedded `gates[]`, WebSocket stream, Pillar 1 artifact persistence.

**Safe to proceed mock-first:** Prototype and OpenAPI contract are sufficient for Next.js + MSW while backend closes P0 gaps.

---

## Priority legend

| Priority | Meaning |
|----------|---------|
| **P0 Critical** | Blocks Phase 1 MVP or breaks a P0 screen on real API |
| **P1 Important** | Required for full 7-pillar journey or P1 screens |
| **P2 Nice to have** | Enterprise, admin, or polish |

---

## Cross-cutting gaps (all screens)

| ID | Gap type | Detail | Backend today | Priority |
|----|----------|--------|---------------|----------|
| X-01 | Response field | `RunRead` missing `idea_text`, `current_pillar`, `cost_usd`, `gates[]`, `workspace_id`, `organization_id`, `started_at`, `completed_at`, `live_url` | `schemas/run.py` — 4 fields only | **P0** |
| X-02 | Response field | `RunStatus` enum mismatch: contract has `queued`, `paused`, `cancelled`; code has `pending` only (no `queued`/`cancelled`) | `schemas/run.py` | **P0** |
| X-03 | Backend impl | Legacy ORM `models/run.py` vs tenant schema `org_*.runs` (F-040) | Risk on all run endpoints | **P0** |
| X-04 | Missing API | `GET /v1/runs/{run_id}/stream` (WebSocket) | Not in `router.py` | **P0** |
| X-05 | Missing API | `GET /v1/runs?status=` filter | `list_runs` has no `status` query param | **P1** |
| X-06 | Missing API | `GET /v1/runs/{run_id}/artifacts?kind=` filter | `list_artifacts` returns all kinds | **P1** |
| X-07 | Backend impl | `POST /v1/ideas` does not call `OrchestratorEngine.create_run()` | `ideas.py` — DB insert only | **P0** |
| X-08 | Backend impl | `POST /v1/ideas` does not persist `idea.text` | `IdeaCreate.text` ignored | **P0** |
| X-09 | Backend impl | `DELETE /v1/runs/{id}` deletes row; no orchestrator cancel | `runs.py` | **P1** |
| X-10 | Backend impl | Agents do not consistently persist artifacts to `artifacts` table | Orchestrator/agents partial | **P0** (P1 screens) |
| X-11 | Backend impl | `cost_ledger` often empty → `GET /v1/llmops/cost` returns `0` | `llmops.py` | **P1** |
| X-12 | Missing API | `GET /v1/llmops/cost/detail` | Not implemented | **P1** |
| X-13 | Missing API | Workspaces CRUD | Not in router | **P1** |
| X-14 | Missing API | Admin tenants / audit-log | Not in router | **P2** |
| X-15 | Backend impl | `GateRead` on `RunRead` — gates not embedded in run GET; separate query N/A | No join in `get_run` | **P0** |
| X-16 | Response field | `GateDecision.notes` not stored on gate row | `gates.py` updates state only | **P1** |
| X-17 | Backend impl | `decided_by` set to `organization_id` not user `sub` | `gates.py` line 50 | **P1** |
| X-18 | Auth | Supabase Auth — no REST; Next.js client only | N/A (by design) | **P0** (frontend) |

---

## Per-screen consistency

### 1. Login

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/login` | `prototype/index.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | — | Supabase Auth (client SDK) | Not applicable to FastAPI | — |
| Missing API | Optional `GET /health` | API reachability check | ✅ `health.py` | P2 |
| Missing response field | — | JWT claims: `sub`, `organization_id`, `role`, `scope` | Supabase config (not API) | **P0** (auth setup) |
| Missing artifact | — | None | — | — |
| Missing backend impl | Supabase SSR session + MFA | `frontend_inventory` AF-051 | ❌ No Next.js app | **P0** |
| Missing WebSocket | — | None | — | — |

---

### 2. Auth callback

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/auth/callback` | Not in prototype | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | — | Supabase token exchange | Client-only | — |
| Missing backend impl | `/auth/callback` route + session cookies | AF-051 | ❌ | **P0** |
| Missing WebSocket | — | None | — | — |

---

### 3. Portal layout shell

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `(portal)/layout` | Implicit on all portal HTML pages | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | — | `GET /v1/llmops/cost` | ✅ Implemented (often `$0`) | — |
| Missing response field | `CostRead.total_cost_usd` only | Prototype also shows per-run cost on header | Per-run `cost_usd` on `RunRead` missing | **P0** |
| Missing response field | Pending gate summary | Gate banner needs `gates[]` on active run | Not on `RunRead` | **P0** |
| Missing artifact | — | None | — | — |
| Missing backend impl | Layout components + cost ticker hook | AF-053 | ❌ Next.js | **P0** |
| Missing WebSocket | Optional gate events via stream | Banner could use WS `gate.required` | ❌ No stream | **P1** |

---

### 4. Idea Intake

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/idea` | `prototype/idea-intake.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | `GET /v1/workspaces` | Locale + workspace selector (inventory) | ❌ Not implemented | **P1** |
| Missing response field | `RunRead` after create: `idea_text`, `current_pillar: 1`, `status: queued` | Prototype redirects to run hub | Returns `pending`, `pillar: "strategy"` only | **P0** |
| Missing response field | `IdeaCreate.locale`, `source_url`, `workspace_id` | Form fields in prototype + inventory | `IdeaCreate` schema: `text` only | **P1** |
| Missing artifact | — | None at submit | — | — |
| Missing backend impl | Orchestrator kickoff after idea create | F-067 | ❌ Not wired | **P0** |
| Missing backend impl | Persist `idea_text` on run | OpenAPI `RunRead.idea_text` | ❌ Not stored | **P0** |
| Missing backend impl | PDF upload / voice (inventory) | Not in prototype | ❌ | **P2** |
| Missing WebSocket | — | None at submit | — | — |

---

### 5. Run List / Dashboard

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/runs` | `prototype/dashboard.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | `GET /v1/runs?status=` | Status filter dropdown in prototype | ❌ No `status` param | **P1** |
| Missing API | `GET /v1/workspaces/{id}/runs` | Inventory P1 | ❌ | **P1** |
| Missing response field | `idea_text` (truncated) | Table column in prototype | ❌ Not on `RunRead` | **P0** |
| Missing response field | `current_pillar` | Stage column "1 · Validate" | ❌ Only legacy `pillar` string | **P0** |
| Missing response field | `cost_usd` | Cost column | ❌ Missing | **P1** |
| Missing response field | `status: awaiting_gate` | Prototype shows "Awaiting gate" | Code uses `pending`/`running`/etc.; no `awaiting_gate` in enum | **P0** |
| Missing artifact | — | None | — | — |
| Missing backend impl | Search by idea text | Search input in prototype | ❌ No search param | **P2** |
| Missing WebSocket | — | None | — | — |

---

### 6. Run Detail (build hub)

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/runs/[id]` | `prototype/run-detail.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | — | `GET /v1/runs/{id}`, `GET artifacts`, `DELETE` | ✅ Routes exist | — |
| Missing response field | `gates[]` with pending gate | Gate banner + studio cards | ❌ Not on `RunRead` | **P0** |
| Missing response field | `idea_text`, `current_pillar`, `cost_usd` | Header + stepper | ❌ Missing | **P0** |
| Missing response field | `started_at`, `completed_at` | Progress timing | ❌ Missing | **P1** |
| Missing artifact | Summary cards per studio | Links show viability, etc. | Empty unless agents wrote rows | **P0** |
| Missing backend impl | Pillar stepper lock/unlock by stage | Prototype greys out studios | No `current_pillar` progression API | **P0** |
| Missing backend impl | Cancel → orchestrator stop | Cancel button in prototype | DELETE only removes DB row | **P1** |
| Missing WebSocket | `GET /v1/runs/{id}/stream` | Live activity log in prototype | ❌ **Not implemented** | **P0** |

---

### 7. Validation Studio

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/runs/[id]/validation` | `prototype/validation-studio.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | — | `GET run`, `GET artifacts`, `POST gate` | ✅ Routes exist | — |
| Missing response field | `GateRead` via run or gate POST response | Approve / Pivot actions | Gate GET not separate; not embedded on run | **P0** |
| Missing response field | `viability` in artifact `meta` | Gauge "72 Moderate" | Depends on artifact `meta` shape | **P0** |
| Missing artifact | `lean_canvas` | Canvas sections in prototype | ❌ Not produced E2E | **P0** |
| Missing artifact | `market_report` | Market tab (inventory) | ❌ Not produced E2E | **P0** |
| Missing artifact | `viability` | Viability gauge | ❌ Not produced E2E | **P0** |
| Missing artifact | `prd` | PRD tab (post-gate) | ❌ Product Planner not in orchestrator post-gate | **P0** |
| Missing backend impl | Pillar 1 chain: Research → Strategy → gate → Product Planner | F-078 | ❌ Partial stub | **P0** |
| Missing backend impl | `validation_approve` gate creation on interrupt | Gate banner | 🟡 Gate model exists; E2E interrupt alignment unclear | **P0** |
| Missing WebSocket | Stream during validation | Inventory lists stream | ❌ | **P1** |

---

### 8. Architecture Studio

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/runs/[id]/architecture` | `prototype/architecture-studio.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | — | `GET run`, `GET artifacts`, `POST gate` | ✅ | — |
| Missing response field | `architecture_approve` gate in `gates[]` | Approve / Reject buttons | Same as X-15 | **P1** |
| Missing artifact | `erd` | Mermaid diagram in prototype | ❌ Architect agent not built | **P1** |
| Missing artifact | `openapi` | API spec tab (inventory) | ❌ | **P1** |
| Missing artifact | `stack` | Stack cards in prototype | ❌ | **P1** |
| Missing artifact | `cost_forecast` | "$142/mo" card | ❌ | **P1** |
| Missing backend impl | Architect Agent (AF-040) | Pillar 2 | ❌ LLD only; orchestrator stub | **P1** |
| Missing backend impl | `architecture_approve` gate workflow | Approve → resume codegen | Gate POST exists; pillar 2 stub | **P1** |
| Missing WebSocket | — | Not required for MVP | — | **P2** |

---

### 9. Code Review Studio

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/runs/[id]/review` | `prototype/code-review.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | — | `GET run`, `GET artifacts` | ✅ | — |
| Missing response field | `review_report` meta: `coverage_pct`, `heal_cycles`, `scans`, `pr_url` | Prototype UI | ❌ No artifact rows | **P1** |
| Missing artifact | `review_report` | Coverage, scans, status | ❌ Reviewer not wired to orchestrator P4 | **P1** |
| Missing artifact | `repo_url` | Open repo / PR links | ❌ Coder not built | **P1** |
| Missing backend impl | Coder Agent (AF-041) | Pillar 3 | ❌ | **P1** |
| Missing backend impl | Reviewer in orchestrator P4 node (F-080) | Self-heal cycles in UI | ❌ Stub node | **P1** |
| Missing WebSocket | Heal cycle live updates | Inventory + prototype implied | ❌ | **P1** |

---

### 10. Deploy Console

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/runs/[id]/deploy` | `prototype/deploy-console.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | — | `GET run`, `GET artifacts`, `POST gate` | ✅ | — |
| Missing response field | `live_url` on `RunRead` | Could shortcut URL display | ❌ Missing on `RunRead` | **P1** |
| Missing artifact | `deploy_url` | Live URL card | ❌ DevOps not built | **P1** |
| Missing artifact | `smoke_test` | Passed / latency in prototype | ❌ | **P1** |
| Missing backend impl | DevOps Agent (AF-043) | Pillar 5 | ❌ Skeleton only | **P1** |
| Missing backend impl | `infra_spend_approve` gate | Spend approval banner | Gate API exists; agent/gate E2E missing | **P1** |
| Missing backend impl | Rollback | Button in prototype | ❌ No API | **P2** |
| Missing WebSocket | Deploy log stream | Terminal log in prototype | ❌ | **P1** |

---

### 11. Launch Control Center

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/runs/[id]/launch` | `prototype/launch-control.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | `POST /v1/feedback` | Thumbs on social draft | ✅ Audit only; no LLMOps consumer | **P1** |
| Missing response field | — | `GET run`, artifacts, gate | Partial | — |
| Missing artifact | `brand_kit` | Brand panel | ❌ Marketing not built | **P1** |
| Missing artifact | `landing_page` | Hero preview | ❌ | **P1** |
| Missing artifact | `social_posts` | LinkedIn draft | ❌ | **P1** |
| Missing artifact | `email_sequences` | Email tab (inventory) | ❌ | **P1** |
| Missing artifact | `blog_drafts` | Blogs tab (inventory) | ❌ | **P1** |
| Missing backend impl | Marketing Agent (AF-044) | Pillar 6 | ❌ LLD only | **P1** |
| Missing backend impl | `launch_approve` gate | Approve launch button | Gate API exists; E2E missing | **P1** |
| Missing WebSocket | — | Not required | — | — |

---

### 12. LLMOps Dashboard

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/llmops` | `prototype/llmops-dashboard.html` | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | `GET /v1/llmops/cost/detail?group_by=` | Charts by model / pillar / run | ❌ Not implemented | **P1** |
| Missing response field | `CostDetailRead.breakdown[]` | Bar charts in prototype | Only `total_cost_usd` exists | **P1** |
| Missing response field | Drift / eval / prompt version data | Prototype tables + alert | ❌ No API surface | **P1** |
| Missing artifact | — | Platform telemetry (not per-run artifacts) | — | — |
| Missing backend impl | LLMOps Agent (AF-045) | Pillar 7 | ❌ Not built | **P1** |
| Missing backend impl | `cost_ledger` population | Non-zero totals | 🟡 Table exists; often empty | **P1** |
| Missing WebSocket | — | None | — | — |

---

### 13. Admin Dashboard

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/admin` | Not in prototype | |

| Category | Item | Contract / UI need | Backend | Priority |
|----------|------|-------------------|---------|----------|
| Missing API | `GET/POST/PATCH/DELETE /v1/admin/tenants` | Tenant CRUD | ❌ | **P2** |
| Missing API | `GET /v1/admin/registries/{type}` | Model/prompt/tool registry | ❌ | **P2** |
| Missing API | `GET /v1/admin/audit-log` | Audit viewer | ❌ (audit writes exist) | **P2** |
| Missing backend impl | Admin UI AF-062 | Full dashboard | ❌ | **P2** |
| Missing WebSocket | — | None | — | — |

---

### 14. Not found

| Field | Inventory route | Prototype | |
|-------|-----------------|-----------|---|
| Route | `/not-found` | Not in prototype | |

| Category | Item | Backend | Priority |
|----------|------|---------|----------|
| Missing backend impl | Next.js `not-found.tsx` only | ❌ | **P2** |

---

## Roll-up tables

### Missing APIs by priority

| Priority | Endpoint / capability | Screens affected |
|----------|----------------------|------------------|
| **P0** | `GET /v1/runs/{id}/stream` (WebSocket) | Run Detail, Validation (optional), Code Review, Deploy |
| **P0** | `POST /v1/ideas` → orchestrator (behavioral gap, not new route) | Idea Intake |
| **P1** | `GET /v1/runs?status=` | Dashboard |
| **P1** | `GET /v1/runs/{id}/artifacts?kind=` | All studios |
| **P1** | `GET /v1/llmops/cost/detail` | LLMOps, layout |
| **P1** | `GET/POST /v1/workspaces`, `GET …/runs` | Idea Intake, Dashboard |
| **P2** | Admin APIs | Admin |
| **P2** | `GET /health` (optional) | Login |

### Missing `RunRead` fields by priority

| Priority | Field | Screens affected |
|----------|-------|------------------|
| **P0** | `idea_text` | Idea Intake, Dashboard, Run Detail, all studios |
| **P0** | `current_pillar` | Dashboard, Run Detail, stepper, sidebar locks |
| **P0** | `gates[]` | Layout banner, Run Detail, all gate studios |
| **P0** | `status` values (`awaiting_gate`, `queued`, `cancelled`) | Dashboard, Run Detail |
| **P1** | `cost_usd` | Dashboard, Run Detail, layout ticker |
| **P1** | `organization_id`, `workspace_id` | All authenticated screens |
| **P1** | `live_url` | Run Detail, Deploy |
| **P1** | `started_at`, `completed_at` | Run Detail |
| **P2** | `idea_meta` | Idea Intake (locale, domain tags) |

### Missing artifacts by priority

| Priority | `kind` | Screen | Agent producer |
|----------|--------|--------|----------------|
| **P0** | `lean_canvas`, `viability`, `market_report`, `prd` | Validation Studio | Research, Strategy, Product Planner |
| **P1** | `erd`, `openapi`, `stack`, `cost_forecast` | Architecture Studio | Architect |
| **P1** | `review_report`, `repo_url` | Code Review | Reviewer, Coder |
| **P1** | `deploy_url`, `smoke_test` | Deploy Console | DevOps |
| **P1** | `brand_kit`, `landing_page`, `social_posts`, `email_sequences`, `blog_drafts` | Launch Control | Marketing |

### Missing backend implementation by priority

| Priority | Component | Impact |
|----------|-----------|--------|
| **P0** | ORM ↔ tenant schema (F-040) | All run/gate/artifact APIs |
| **P0** | Ideas → orchestrator + `idea_text` (F-052, F-067) | Idea Intake |
| **P0** | Pillar 1 agent chain + artifact persistence (F-078, F-039) | Validation Studio |
| **P0** | WebSocket stream (F-059) | Run Detail live log |
| **P0** | Next.js + Supabase (AF-051–053) | All screens |
| **P1** | Pillars 2–7 agents + orchestrator wiring | Architecture → Launch |
| **P1** | Reviewer on P4 node (F-080) | Code Review |
| **P1** | Cost ledger population (F-038) | LLMOps, layout |
| **P1** | Feedback → LLMOps consumer | Launch Control |
| **P2** | Admin APIs + UI | Admin |
| **P2** | Rollback API | Deploy Console |

### WebSocket support by screen

| Screen | Prototype shows live log? | Inventory requires WS? | Backend | Priority |
|--------|---------------------------|------------------------|---------|----------|
| Run Detail | Yes | Yes | ❌ | **P0** |
| Validation Studio | No | Optional | ❌ | **P1** |
| Code Review | No (static heal) | Yes | ❌ | **P1** |
| Deploy Console | Yes | Yes | ❌ | **P1** |
| All others | No | No | — | — |

---

## Prototype vs inventory route map

| Prototype file | Inventory route | Match? |
|----------------|-----------------|--------|
| `index.html` | `/login` | ✅ |
| — | `/auth/callback` | ❌ Prototype gap |
| `idea-intake.html` | `/idea` | ✅ |
| `dashboard.html` | `/runs` | ✅ |
| `run-detail.html` | `/runs/[id]` | ✅ |
| `validation-studio.html` | `/runs/[id]/validation` | ✅ |
| `architecture-studio.html` | `/runs/[id]/architecture` | ✅ |
| `code-review.html` | `/runs/[id]/review` | ✅ |
| `deploy-console.html` | `/runs/[id]/deploy` | ✅ |
| `launch-control.html` | `/runs/[id]/launch` | ✅ |
| `llmops-dashboard.html` | `/llmops` | ✅ |
| — | `/admin` | ❌ Prototype gap |
| — | `/not-found` | ❌ Prototype gap |

---

## Backend endpoint implementation matrix

| Endpoint | In OpenAPI | In api_inventory | Implemented | Notes |
|----------|------------|------------------|-------------|-------|
| `GET /health` | ✅ | ✅ | ✅ | |
| `POST /v1/ideas` | ✅ | 🟡 | 🟡 | No text persist, no orchestrator |
| `GET /v1/runs` | ✅ | 🟡 | 🟡 | Pagination OK; schema thin |
| `GET /v1/runs/{id}` | ✅ | 🟡 | 🟡 | 4-field `RunRead` |
| `DELETE /v1/runs/{id}` | ✅ | ✅ | 🟡 | No orchestrator cancel |
| `GET /v1/runs/{id}/artifacts` | ✅ | 🟡 | 🟡 | No `kind` filter |
| `POST /v1/runs/{id}/gates/{id}` | ✅ | 🟡 | 🟡 | Resume wired in dev |
| `GET /v1/runs/{id}/stream` | ✅ planned | ❌ | ❌ | **P0 gap** |
| `POST /v1/feedback` | ✅ | 🟡 | 🟡 | Audit only |
| `GET /v1/llmops/cost` | ✅ | 🟡 | 🟡 | Often zero |
| `GET /v1/llmops/cost/detail` | ✅ planned | ❌ | ❌ | P1 |
| Workspaces | ✅ planned | ❌ | ❌ | P1 |
| Admin | ✅ planned | ❌ | ❌ | P2 |

---

## Recommendations

1. **Do not block Next.js on backend** — use MSW fixtures shaped to `docs/openapi.yaml` until P0 backend items land.  
2. **Somesh P0 sprint:** F-040, F-052, F-067, expand `RunRead`, embed `gates[]`, F-059 WebSocket, F-078 + F-039.  
3. **OpenAPI:** Add remaining `ArtifactMeta*` schemas for `market_report`, `prd`, `openapi`, `stack`, `repo_url`, `email_sequences`, `blog_drafts`.  
4. **Raunak:** Implement polling fallback for Run Detail until WebSocket ships.  
5. **Re-run this report** when `RunRead` matches OpenAPI and first P1 artifacts appear in integration tests.

---

## Document references

| Document | Path |
|----------|------|
| Frontend inventory | `raunak-docs/frontend_inventory.md` |
| API inventory | `raunak-docs/api_inventory.md` |
| OpenAPI contract | `docs/openapi.yaml` |
| Review package | `docs/review_package_v1.md` |
| Frontend checklist | `docs/frontend_review_checklist.md` |
| Static prototype | `prototype/` |
| Backend routes | `PROJECT-1-AutoFounder-AI/backend/app/api/v1/` |

---

*Consistency report v1.0 — June 2026*
