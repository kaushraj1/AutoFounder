# AutoFounder AI — API Inventory (Founder Portal)

> **Format:** OpenAPI 3.1  
> **Base URL:** `https://api.autofounder.ai/v1` (prod) · `http://localhost:8000/v1` (local)  
> **Auth:** `Authorization: Bearer <Supabase JWT>` on all `/v1/*` routes  
> **Companion:** [frontend_inventory.md](./frontend_inventory.md)  
> **Backend source:** `backend/app/schemas/*`, `backend/app/api/v1/*`, `.claude/specs/api-design.md`

**Implementation note:** `RunRead` in code today exposes only `id`, `pillar`, `status`, `created_at`. This inventory documents the **frontend target contract** (includes `idea_text`, `current_pillar`, `cost_usd`, `gates`) aligned with the database spec and api-design. Marked with `x-schema-status` where backend lags.

---

## Screen → endpoint matrix

| Screen | Endpoint | Method | Auth | Status |
|--------|----------|--------|------|--------|
| Login | — (Supabase Auth) | — | Public | Client SDK |
| Login | `/health` | GET | None | ✅ Implemented |
| Auth callback | — (Supabase token exchange) | — | Public | Client SDK |
| Portal layout shell | `/v1/llmops/cost` | GET | Bearer JWT | ✅ Implemented |
| Portal layout shell | `/v1/runs/{run_id}` | GET | Bearer JWT | 🟡 Partial schema |
| Idea Intake | `/v1/ideas` | POST | Bearer JWT | 🟡 Partial (orchestrator not wired) |
| Idea Intake | `/v1/workspaces` | GET | Bearer JWT | ❌ Planned |
| Run List | `/v1/runs` | GET | Bearer JWT | 🟡 Partial schema |
| Run Detail | `/v1/runs/{run_id}` | GET | Bearer JWT | 🟡 Partial schema |
| Run Detail | `/v1/runs/{run_id}/artifacts` | GET | Bearer JWT | ✅ Implemented |
| Run Detail | `/v1/runs/{run_id}/stream` | WebSocket | Bearer JWT | ❌ Planned |
| Run Detail | `/v1/runs/{run_id}` | DELETE | Bearer JWT | ✅ Implemented |
| Validation Studio | `/v1/runs/{run_id}` | GET | Bearer JWT | 🟡 |
| Validation Studio | `/v1/runs/{run_id}/artifacts` | GET | Bearer JWT | ✅ |
| Validation Studio | `/v1/runs/{run_id}/gates/{gate_id}` | POST | Bearer JWT | ✅ |
| Validation Studio | `/v1/runs/{run_id}/stream` | WebSocket | Bearer JWT | ❌ |
| Architecture Studio | `/v1/runs/{run_id}` | GET | Bearer JWT | 🟡 |
| Architecture Studio | `/v1/runs/{run_id}/artifacts` | GET | Bearer JWT | ✅ |
| Architecture Studio | `/v1/runs/{run_id}/gates/{gate_id}` | POST | Bearer JWT | ✅ |
| Code Review Studio | `/v1/runs/{run_id}` | GET | Bearer JWT | 🟡 |
| Code Review Studio | `/v1/runs/{run_id}/artifacts` | GET | Bearer JWT | ✅ |
| Code Review Studio | `/v1/runs/{run_id}/stream` | WebSocket | Bearer JWT | ❌ |
| Deploy Console | `/v1/runs/{run_id}` | GET | Bearer JWT | 🟡 |
| Deploy Console | `/v1/runs/{run_id}/artifacts` | GET | Bearer JWT | ✅ |
| Deploy Console | `/v1/runs/{run_id}/gates/{gate_id}` | POST | Bearer JWT | ✅ |
| Deploy Console | `/v1/runs/{run_id}/stream` | WebSocket | Bearer JWT | ❌ |
| Launch Control Center | `/v1/runs/{run_id}` | GET | Bearer JWT | 🟡 |
| Launch Control Center | `/v1/runs/{run_id}/artifacts` | GET | Bearer JWT | ✅ |
| Launch Control Center | `/v1/runs/{run_id}/gates/{gate_id}` | POST | Bearer JWT | ✅ |
| Launch Control Center | `/v1/feedback` | POST | Bearer JWT | ✅ |
| LLMOps Dashboard | `/v1/llmops/cost` | GET | Bearer JWT | ✅ |
| LLMOps Dashboard | `/v1/llmops/cost/detail` | GET | Bearer JWT | ❌ Planned |
| Admin Dashboard | `/v1/admin/tenants` | GET/POST/PATCH/DELETE | Bearer JWT + `super_admin` | ❌ Planned |
| Admin Dashboard | `/v1/admin/registries/{type}` | GET/PATCH | Bearer JWT + `super_admin` | ❌ Planned |
| Admin Dashboard | `/v1/admin/audit-log` | GET | Bearer JWT + `super_admin` | ❌ Planned |
| Global not found | — | — | — | No API |

---

## Per-screen API detail (OpenAPI operations)

### 1. Login (`/login`)

**No REST auth endpoints** — Supabase Auth handles login. Optional health check:

```yaml
/health:
  get:
    operationId: getHealth
    tags: [System]
    summary: Liveness probe
    security: []
    responses:
      "200":
        description: Service healthy
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/HealthResponse"
            example:
              status: ok
              service: autofounder-api
              version: "0.1.0"
              env: development
```

**Auth requirements:** None for `/health`. Login screen uses Supabase (`NEXT_PUBLIC_SUPABASE_URL`).

**Mock (Supabase session claims — not OpenAPI):**

```json
{
  "sub": "usr_01jabc123",
  "organization_id": "org_01jdef456",
  "role": "founder",
  "scope": "runs:read runs:write gates:decide"
}
```

---

### 2. Auth callback (`/auth/callback`)

Client-side Supabase OAuth code exchange. No AutoFounder REST call.

---

### 3. Portal layout shell (`(portal)/layout`)

```yaml
/v1/llmops/cost:
  get:
    operationId: getCostTelemetry
    tags: [LLMOps]
    summary: Org-wide FinOps cost total
    security:
      - bearerAuth: []
    responses:
      "200":
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CostEnvelope"
            example:
              data:
                total_cost_usd: 12.47
              meta:
                request_id: af-req-01jmock001
                timestamp: "2026-06-09T10:00:00Z"
      "401":
        $ref: "#/components/responses/Unauthorized"
```

---

### 4. Idea Intake (`/idea`)

```yaml
/v1/ideas:
  post:
    operationId: submitIdea
    tags: [Ideas]
    summary: Submit startup idea and start a run
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/IdeaCreate"
          example:
            text: "A subscription app that helps dog owners find trusted walkers in Bangalore."
    responses:
      "201":
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RunEnvelope"
            example:
              data:
                id: "550e8400-e29b-41d4-a716-446655440000"
                workspace_id: "660e8400-e29b-41d4-a716-446655440001"
                organization_id: "770e8400-e29b-41d4-a716-446655440002"
                status: queued
                current_pillar: 1
                idea_text: "A subscription app that helps dog owners find trusted walkers in Bangalore."
                cost_usd: 0
                gates: []
                created_at: "2026-06-09T10:00:00Z"
              meta:
                request_id: af-req-01jmock002
                timestamp: "2026-06-09T10:00:00Z"
      "400":
        $ref: "#/components/responses/ValidationError"
      "402":
        $ref: "#/components/responses/CostCapExceeded"
      "429":
        $ref: "#/components/responses/RateLimited"
```

**Auth:** Bearer JWT · scopes: `runs:write` · MFA enforced (Supabase).

---

### 5. Run List (`/runs`)

```yaml
/v1/runs:
  get:
    operationId: listRuns
    tags: [Runs]
    summary: List runs with cursor pagination
    security:
      - bearerAuth: []
    parameters:
      - name: limit
        in: query
        schema: { type: integer, default: 25, minimum: 1, maximum: 100 }
      - name: cursor
        in: query
        schema: { type: string }
      - name: order
        in: query
        schema: { type: string, enum: [asc, desc], default: desc }
      - name: status
        in: query
        schema: { $ref: "#/components/schemas/RunStatus" }
        description: Filter (frontend target — not yet in backend)
    responses:
      "200":
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RunListEnvelope"
            example:
              data:
                - id: "550e8400-e29b-41d4-a716-446655440000"
                  status: awaiting_gate
                  current_pillar: 1
                  idea_text: "Dog walker subscription app..."
                  cost_usd: 2.14
                  created_at: "2026-06-09T09:30:00Z"
                - id: "550e8400-e29b-41d4-a716-446655440099"
                  status: completed
                  current_pillar: 7
                  idea_text: "AI resume builder for students"
                  cost_usd: 8.92
                  created_at: "2026-06-08T14:00:00Z"
              pagination:
                cursor: "eyJpZCI6IjU1MGU4NDAwIn0="
                has_more: true
                total: 42
              meta:
                request_id: af-req-01jmock003
                timestamp: "2026-06-09T10:00:00Z"
```

**Auth:** Bearer JWT · scopes: `runs:read`

---

### 6. Run Detail shell (`/runs/[id]`)

```yaml
/v1/runs/{run_id}:
  get:
    operationId: getRun
    tags: [Runs]
    security:
      - bearerAuth: []
    parameters:
      - $ref: "#/components/parameters/RunId"
    responses:
      "200":
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RunEnvelope"
            example:
              data:
                id: "550e8400-e29b-41d4-a716-446655440000"
                workspace_id: "660e8400-e29b-41d4-a716-446655440001"
                organization_id: "770e8400-e29b-41d4-a716-446655440002"
                status: running
                current_pillar: 1
                idea_text: "A subscription app that helps dog owners find trusted walkers in Bangalore."
                cost_usd: 1.23
                gates:
                  - id: "880e8400-e29b-41d4-a716-446655440003"
                    kind: validation_approve
                    state: pending
                    payload: {}
                    created_at: "2026-06-09T10:15:00Z"
                created_at: "2026-06-09T10:00:00Z"
                started_at: "2026-06-09T10:00:05Z"
              meta:
                request_id: af-req-01jmock004
                timestamp: "2026-06-09T10:16:00Z"
      "404":
        $ref: "#/components/responses/NotFound"
  delete:
    operationId: cancelRun
    tags: [Runs]
    security:
      - bearerAuth: []
    parameters:
      - $ref: "#/components/parameters/RunId"
    responses:
      "200":
        content:
          application/json:
            example:
              data: true
              meta:
                request_id: af-req-01jmock005
                timestamp: "2026-06-09T10:20:00Z"

/v1/runs/{run_id}/artifacts:
  get:
    operationId: listArtifacts
    tags: [Artifacts]
    security:
      - bearerAuth: []
    parameters:
      - $ref: "#/components/parameters/RunId"
      - name: kind
        in: query
        schema: { $ref: "#/components/schemas/ArtifactKind" }
        description: Filter by artifact type (frontend target)
    responses:
      "200":
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ArtifactListEnvelope"
            example:
              data:
                - id: "aa0e8400-e29b-41d4-a716-446655440010"
                  run_id: "550e8400-e29b-41d4-a716-446655440000"
                  kind: lean_canvas
                  uri: "s3://artifacts/org_770e/lean_canvas.json"
                  meta:
                    viability_score: 72
                    viability_band: moderate
                  created_at: "2026-06-09T10:14:00Z"
              meta:
                request_id: af-req-01jmock006
                timestamp: "2026-06-09T10:16:00Z"
```

**WebSocket** (`GET /v1/runs/{run_id}/stream`):

```yaml
/v1/runs/{run_id}/stream:
  get:
    operationId: streamRunEvents
    tags: [Runs]
    summary: WebSocket upgrade for live step events
    security:
      - bearerAuth: []
    parameters:
      - $ref: "#/components/parameters/RunId"
      - name: Last-Event-ID
        in: header
        schema: { type: string }
        description: Replay step_events from this id (30 min window)
    responses:
      "101":
        description: Switching Protocols (WebSocket)
    x-websocket-messages:
      serverToClient:
        - example: { "type": "step.started", "step_id": "s1", "agent_id": "strategy.v1", "at": "2026-06-09T10:01:00Z" }
        - example: { "type": "token", "content": "Analyzing market size...", "step_id": "s1" }
        - example: { "type": "gate.required", "gate_id": "880e8400-e29b-41d4-a716-446655440003", "kind": "validation_approve", "payload": {} }
        - example: { "type": "run.completed", "run_id": "550e8400-e29b-41d4-a716-446655440000", "cost_usd": 4.56 }
      clientToServer:
        - example: { "type": "ping" }
```

**Mock stream fixture:** `mock_step_events.json`

---

### 7. Validation Studio (`/runs/[id]/validation`)

Uses: `getRun`, `listArtifacts` (kinds: `lean_canvas`, `market_report`, `prd`, `viability`), `decideGate`, `streamRunEvents`.

```yaml
/v1/runs/{run_id}/gates/{gate_id}:
  post:
    operationId: decideGate
    tags: [Gates]
    summary: Approve, reject, or pivot at a HITL gate
    security:
      - bearerAuth: []
    parameters:
      - $ref: "#/components/parameters/RunId"
      - $ref: "#/components/parameters/GateId"
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/GateDecision"
          examples:
            approve:
              value: { "decision": "approved", "notes": "Strong market signal, proceed." }
            pivot:
              value: { "decision": "rejected", "notes": "Pivot to B2B corporate dog-care benefits." }
    responses:
      "200":
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/GateEnvelope"
            example:
              data:
                id: "880e8400-e29b-41d4-a716-446655440003"
                run_id: "550e8400-e29b-41d4-a716-446655440000"
                kind: validation_approve
                state: approved
                decided_by: "usr_01jabc123"
                decided_at: "2026-06-09T10:20:00Z"
                payload: {}
                created_at: "2026-06-09T10:15:00Z"
              meta:
                request_id: af-req-01jmock007
                timestamp: "2026-06-09T10:20:00Z"
      "409":
        $ref: "#/components/responses/Conflict"
```

**Artifact mock (`lean_canvas` meta):**

```json
{
  "problem": ["Dog owners struggle to find reliable walkers"],
  "customer_segments": ["Urban pet owners", "Working professionals"],
  "unique_value_proposition": "Verified walkers with real-time GPS tracking",
  "solution": ["Mobile app", "Walker vetting", "Subscription billing"],
  "unfair_advantage": "Hyperlocal trust network",
  "early_adopters": "Bangalore apartment communities"
}
```

---

### 8. Architecture Studio (`/runs/[id]/architecture`)

Uses: `getRun`, `listArtifacts` (kinds: `erd`, `openapi`, `stack`, `cost_forecast`), `decideGate` (`architecture_approve`).

**Mock artifact (`erd` + `openapi`):**

```json
{
  "kind": "erd",
  "meta": {
    "mermaid": "erDiagram\n  USER ||--o{ BOOKING : makes\n  WALKER ||--o{ BOOKING : fulfills",
    "cost_forecast_usd": 85.50,
    "stack": [
      { "layer": "frontend", "choice": "Next.js 14", "rationale": "SSR + SEO" },
      { "layer": "backend", "choice": "FastAPI", "rationale": "Agent ecosystem fit" }
    ]
  }
}
```

---

### 9. Code Review Studio (`/runs/[id]/review`)

Uses: `getRun`, `listArtifacts` (kinds: `review_report`, `repo_url`), `streamRunEvents`.

**Mock artifact (`review_report`):**

```json
{
  "kind": "review_report",
  "meta": {
    "coverage_pct": 84.2,
    "heal_cycles": 2,
    "max_cycles": 5,
    "status": "passed",
    "scans": [
      { "tool": "trivy", "severity": "LOW", "count": 1 },
      { "tool": "semgrep", "severity": "NONE", "count": 0 }
    ],
    "repo_url": "https://github.com/founder/dogwalker-mvp",
    "pr_url": "https://github.com/founder/dogwalker-mvp/pull/1"
  }
}
```

---

### 10. Deploy Console (`/runs/[id]/deploy`)

Uses: `getRun`, `listArtifacts` (kinds: `deploy_url`, `smoke_test`), `decideGate` (`infra_spend_approve`), `streamRunEvents`.

**Mock artifact:**

```json
{
  "kind": "deploy_url",
  "uri": "https://dogwalker-demo.autofounder.ai",
  "meta": {
    "infra_cost_usd": 42.00,
    "smoke_test": { "passed": true, "latency_ms": 210 },
    "region": "ap-south-1"
  }
}
```

---

### 11. Launch Control Center (`/runs/[id]/launch`)

Uses: `getRun`, `listArtifacts` (kinds: `brand_kit`, `landing_page`, `social_posts`, `email_sequences`), `decideGate` (`launch_approve`), `submitFeedback`.

```yaml
/v1/feedback:
  post:
    operationId: submitFeedback
    tags: [LLMOps]
    security:
      - bearerAuth: []
    requestBody:
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/FeedbackCreate"
          example:
            run_id: "550e8400-e29b-41d4-a716-446655440000"
            step_id: "marketing.launch_draft"
            rating: 4
            comment: "Tone is good; shorten the hero headline."
    responses:
      "200":
        example:
          data: true
          meta:
            request_id: af-req-01jmock008
            timestamp: "2026-06-09T12:00:00Z"
```

---

### 12. LLMOps Dashboard (`/llmops`)

Primary: `GET /v1/llmops/cost` (implemented).

**Planned extension** for charts:

```yaml
/v1/llmops/cost/detail:
  get:
    operationId: getCostDetail
    tags: [LLMOps]
    x-implementation-status: planned
    security:
      - bearerAuth: []
    parameters:
      - name: group_by
        in: query
        schema: { type: string, enum: [model, pillar, run] }
    responses:
      "200":
        example:
          data:
            total_cost_usd: 12.47
            breakdown:
              - key: "gemini-3.5-flash"
                cost_usd: 9.80
              - key: "pillar_1"
                cost_usd: 4.20
          meta:
            request_id: af-req-01jmock009
            timestamp: "2026-06-09T10:00:00Z"
```

---

### 13. Admin Dashboard (`/admin`) — planned

```yaml
/v1/admin/tenants:
  get:
    operationId: listTenants
    x-implementation-status: planned
    security:
      - bearerAuth: []
    x-required-role: super_admin
    responses:
      "200":
        example:
          data:
            - id: "org_01jdef456"
              name: "Acme Founders"
              tier: startup
              status: active
          meta:
            request_id: af-req-01jmock010
            timestamp: "2026-06-09T10:00:00Z"
```

---

### 14. Global not found

No API calls.

---

## Complete OpenAPI 3.1 specification

```yaml
openapi: 3.1.0
info:
  title: AutoFounder AI — Founder Portal API
  version: 1.0.0
  description: |
    REST surface consumed by the Next.js Founder Portal.
    WebSocket stream documented under `/v1/runs/{run_id}/stream`.
    Supabase Auth is used for human login (not part of this spec).

servers:
  - url: https://api.autofounder.ai/v1
    description: Production
  - url: https://api-staging.autofounder.ai/v1
    description: Staging
  - url: http://localhost:8000/v1
    description: Local

tags:
  - name: System
  - name: Ideas
  - name: Runs
  - name: Gates
  - name: Artifacts
  - name: LLMOps
  - name: Workspaces
  - name: Admin

security:
  - bearerAuth: []

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        Supabase JWT. Required claims: sub, organization_id, role, scope.
        MFA enforced for human accounts.

  parameters:
    RunId:
      name: run_id
      in: path
      required: true
      schema: { type: string, format: uuid }
    GateId:
      name: gate_id
      in: path
      required: true
      schema: { type: string, format: uuid }

  responses:
    Unauthorized:
      description: Missing or invalid token
      content:
        application/json:
          schema: { $ref: "#/components/schemas/ErrorEnvelope" }
          example:
            error:
              code: AF_ERR_UNAUTHORIZED
              message: Missing or invalid token
            meta:
              request_id: af-req-err401
              timestamp: "2026-06-09T10:00:00Z"
    NotFound:
      description: Resource not found
      content:
        application/json:
          example:
            error:
              code: AF_ERR_NOT_FOUND
              message: Run not found
            meta:
              request_id: af-req-err404
              timestamp: "2026-06-09T10:00:00Z"
    ValidationError:
      description: Request validation failed
      content:
        application/json:
          example:
            error:
              code: AF_ERR_VALIDATION
              message: idea text must be at least 10 characters
            meta:
              request_id: af-req-err400
              timestamp: "2026-06-09T10:00:00Z"
    Conflict:
      description: State conflict
      content:
        application/json:
          example:
            error:
              code: AF_ERR_GATE_ALREADY_DECIDED
              message: Gate has already been decided
              details: { gate_id: "880e8400-e29b-41d4-a716-446655440003", current_state: approved }
            meta:
              request_id: af-req-err409
              timestamp: "2026-06-09T10:00:00Z"
    CostCapExceeded:
      description: Monthly cost cap exceeded
      content:
        application/json:
          example:
            error:
              code: AF_ERR_COST_CAP_EXCEEDED
              message: Organization monthly cost limit reached
            meta:
              request_id: af-req-err402
              timestamp: "2026-06-09T10:00:00Z"
    RateLimited:
      description: Too many requests
      headers:
        Retry-After: { schema: { type: integer } }
        X-RateLimit-Limit: { schema: { type: integer } }
        X-RateLimit-Remaining: { schema: { type: integer } }
      content:
        application/json:
          example:
            error:
              code: AF_ERR_RATE_LIMITED
              message: Too many requests
            meta:
              request_id: af-req-err429
              timestamp: "2026-06-09T10:00:00Z"

  schemas:
    Meta:
      type: object
      required: [request_id, timestamp]
      properties:
        request_id: { type: string, example: af-req-01jmock001 }
        timestamp: { type: string, format: date-time }

    ErrorDetail:
      type: object
      required: [code, message]
      properties:
        code: { type: string, example: AF_ERR_NOT_FOUND }
        message: { type: string }
        details: { type: object, additionalProperties: true }

    ErrorEnvelope:
      type: object
      required: [error, meta]
      properties:
        error: { $ref: "#/components/schemas/ErrorDetail" }
        meta: { $ref: "#/components/schemas/Meta" }

    HealthResponse:
      type: object
      required: [status, service, version, env]
      properties:
        status: { type: string, example: ok }
        service: { type: string, example: autofounder-api }
        version: { type: string }
        env: { type: string }

    IdeaCreate:
      type: object
      required: [text]
      properties:
        text:
          type: string
          minLength: 10
          maxLength: 10000
          description: Raw startup idea in plain text
        locale:
          type: string
          example: en-IN
          description: Frontend target — not in current backend schema
        source_url:
          type: string
          format: uri
          description: Frontend target — optional reference URL
        workspace_id:
          type: string
          format: uuid
          description: Frontend target — defaults to org default workspace

    RunStatus:
      type: string
      enum: [queued, running, paused, awaiting_gate, completed, failed, cancelled]
      description: |
        Backend today uses pending|running|awaiting_gate|completed|failed.
        Target aligns with database spec (queued, paused, cancelled added).

    GateKind:
      type: string
      enum: [validation_approve, architecture_approve, infra_spend_approve, launch_approve, canary_rollout]

    GateState:
      type: string
      enum: [pending, approved, rejected, timed_out]

    GateRead:
      type: object
      required: [id, run_id, kind, state, created_at]
      properties:
        id: { type: string, format: uuid }
        run_id: { type: string, format: uuid }
        kind: { $ref: "#/components/schemas/GateKind" }
        state: { $ref: "#/components/schemas/GateState" }
        payload: { type: object, additionalProperties: true }
        decided_by: { type: string, nullable: true }
        decided_at: { type: string, format: date-time, nullable: true }
        timeout_at: { type: string, format: date-time, nullable: true }
        created_at: { type: string, format: date-time }

    GateDecision:
      type: object
      required: [decision]
      properties:
        decision:
          type: string
          enum: [approved, rejected]
          description: Use rejected + notes for pivot flow on validation gate
        notes:
          type: string
          nullable: true
          maxLength: 2000

    RunRead:
      type: object
      required: [id, status, created_at]
      properties:
        id: { type: string, format: uuid }
        workspace_id: { type: string, format: uuid, x-schema-status: target }
        organization_id: { type: string, format: uuid, x-schema-status: target }
        status: { $ref: "#/components/schemas/RunStatus" }
        current_pillar:
          type: integer
          minimum: 1
          maximum: 7
          x-schema-status: target
        idea_text:
          type: string
          x-schema-status: target
        idea_meta: { type: object, x-schema-status: target }
        cost_usd:
          type: number
          format: float
          x-schema-status: target
        gates:
          type: array
          items: { $ref: "#/components/schemas/GateRead" }
          x-schema-status: target
        pillar:
          type: string
          deprecated: true
          description: Legacy field — use current_pillar
        created_at: { type: string, format: date-time }
        started_at: { type: string, format: date-time, nullable: true, x-schema-status: target }
        completed_at: { type: string, format: date-time, nullable: true, x-schema-status: target }

    ArtifactKind:
      type: string
      enum:
        - lean_canvas
        - market_report
        - viability
        - prd
        - erd
        - openapi
        - stack
        - cost_forecast
        - review_report
        - repo_url
        - deploy_url
        - smoke_test
        - brand_kit
        - landing_page
        - social_posts
        - email_sequences
        - blog_drafts

    ArtifactRead:
      type: object
      required: [id, run_id, kind, uri, created_at]
      properties:
        id: { type: string, format: uuid }
        run_id: { type: string, format: uuid }
        kind: { type: string }
        uri: { type: string }
        meta: { type: object, additionalProperties: true, nullable: true }
        created_at: { type: string, format: date-time }

    CostRead:
      type: object
      required: [total_cost_usd]
      properties:
        total_cost_usd: { type: number, format: float }

    FeedbackCreate:
      type: object
      required: [run_id, rating]
      properties:
        run_id: { type: string, format: uuid }
        step_id: { type: string, nullable: true }
        rating: { type: integer, minimum: 1, maximum: 5 }
        comment: { type: string, nullable: true }

    WorkspaceRead:
      type: object
      x-implementation-status: planned
      properties:
        id: { type: string, format: uuid }
        name: { type: string }
        description: { type: string, nullable: true }
        created_at: { type: string, format: date-time }

    PaginationInfo:
      type: object
      properties:
        cursor: { type: string, nullable: true }
        has_more: { type: boolean }
        total: { type: integer }

    RunEnvelope:
      type: object
      required: [data, meta]
      properties:
        data: { $ref: "#/components/schemas/RunRead" }
        meta: { $ref: "#/components/schemas/Meta" }

    RunListEnvelope:
      type: object
      required: [data, pagination, meta]
      properties:
        data:
          type: array
          items: { $ref: "#/components/schemas/RunRead" }
        pagination: { $ref: "#/components/schemas/PaginationInfo" }
        meta: { $ref: "#/components/schemas/Meta" }

    GateEnvelope:
      type: object
      required: [data, meta]
      properties:
        data: { $ref: "#/components/schemas/GateRead" }
        meta: { $ref: "#/components/schemas/Meta" }

    ArtifactListEnvelope:
      type: object
      required: [data, meta]
      properties:
        data:
          type: array
          items: { $ref: "#/components/schemas/ArtifactRead" }
        meta: { $ref: "#/components/schemas/Meta" }

    CostEnvelope:
      type: object
      required: [data, meta]
      properties:
        data: { $ref: "#/components/schemas/CostRead" }
        meta: { $ref: "#/components/schemas/Meta" }

    StreamEvent:
      type: object
      required: [type]
      properties:
        type:
          type: string
          enum:
            - step.started
            - token
            - tool.call
            - step.completed
            - gate.required
            - run.completed
            - run.failed
        step_id: { type: string }
        agent_id: { type: string }
        content: { type: string }
        tool: { type: string }
        args: { type: object }
        gate_id: { type: string, format: uuid }
        kind: { $ref: "#/components/schemas/GateKind" }
        payload: { type: object }
        run_id: { type: string, format: uuid }
        cost_usd: { type: number }
        error: { type: string }
        at: { type: string, format: date-time }

paths:
  /health:
    get:
      operationId: getHealth
      tags: [System]
      summary: Liveness probe
      security: []
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema: { $ref: "#/components/schemas/HealthResponse" }

  /v1/ideas:
    post:
      operationId: submitIdea
      tags: [Ideas]
      summary: Submit idea and create run
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/IdeaCreate" }
      responses:
        "201": { description: Run created, content: { application/json: { schema: { $ref: "#/components/schemas/RunEnvelope" } } } }
        "400": { $ref: "#/components/responses/ValidationError" }
        "401": { $ref: "#/components/responses/Unauthorized" }
        "402": { $ref: "#/components/responses/CostCapExceeded" }
        "429": { $ref: "#/components/responses/RateLimited" }

  /v1/runs:
    get:
      operationId: listRuns
      tags: [Runs]
      summary: List runs (cursor pagination)
      parameters:
        - { name: limit, in: query, schema: { type: integer, default: 25 } }
        - { name: cursor, in: query, schema: { type: string } }
        - { name: order, in: query, schema: { type: string, enum: [asc, desc], default: desc } }
      responses:
        "200": { description: OK, content: { application/json: { schema: { $ref: "#/components/schemas/RunListEnvelope" } } } }
        "401": { $ref: "#/components/responses/Unauthorized" }

  /v1/runs/{run_id}:
    get:
      operationId: getRun
      tags: [Runs]
      parameters: [ { $ref: "#/components/parameters/RunId" } ]
      responses:
        "200": { description: OK, content: { application/json: { schema: { $ref: "#/components/schemas/RunEnvelope" } } } }
        "404": { $ref: "#/components/responses/NotFound" }
    delete:
      operationId: cancelRun
      tags: [Runs]
      parameters: [ { $ref: "#/components/parameters/RunId" } ]
      responses:
        "200": { description: Cancelled }

  /v1/runs/{run_id}/gates/{gate_id}:
    post:
      operationId: decideGate
      tags: [Gates]
      parameters:
        - { $ref: "#/components/parameters/RunId" }
        - { $ref: "#/components/parameters/GateId" }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/GateDecision" }
      responses:
        "200": { description: OK, content: { application/json: { schema: { $ref: "#/components/schemas/GateEnvelope" } } } }
        "409": { $ref: "#/components/responses/Conflict" }

  /v1/runs/{run_id}/artifacts:
    get:
      operationId: listArtifacts
      tags: [Artifacts]
      parameters:
        - { $ref: "#/components/parameters/RunId" }
        - { name: kind, in: query, schema: { $ref: "#/components/schemas/ArtifactKind" } }
      responses:
        "200": { description: OK, content: { application/json: { schema: { $ref: "#/components/schemas/ArtifactListEnvelope" } } } }

  /v1/runs/{run_id}/stream:
    get:
      operationId: streamRunEvents
      tags: [Runs]
      summary: WebSocket upgrade for live events
      x-implementation-status: planned
      parameters:
        - { $ref: "#/components/parameters/RunId" }
      responses:
        "101": { description: Switching Protocols }

  /v1/feedback:
    post:
      operationId: submitFeedback
      tags: [LLMOps]
      requestBody:
        content:
          application/json:
            schema: { $ref: "#/components/schemas/FeedbackCreate" }
      responses:
        "200": { description: Accepted }

  /v1/llmops/cost:
    get:
      operationId: getCostTelemetry
      tags: [LLMOps]
      responses:
        "200": { description: OK, content: { application/json: { schema: { $ref: "#/components/schemas/CostEnvelope" } } } }

  /v1/workspaces:
    get:
      operationId: listWorkspaces
      tags: [Workspaces]
      x-implementation-status: planned
      responses:
        "200": { description: OK }
    post:
      operationId: createWorkspace
      tags: [Workspaces]
      x-implementation-status: planned
      responses:
        "201": { description: Created }

  /v1/workspaces/{workspace_id}/runs:
    get:
      operationId: listWorkspaceRuns
      tags: [Workspaces]
      x-implementation-status: planned
      parameters:
        - { name: workspace_id, in: path, required: true, schema: { type: string, format: uuid } }
      responses:
        "200": { description: OK }
```

---

## Mock response quick reference (MSW)

| Fixture file | Endpoint | Method |
|--------------|----------|--------|
| `mock_idea_submit_response.json` | `/v1/ideas` | POST |
| `mock_runs_list.json` | `/v1/runs` | GET |
| `mock_run_detail.json` | `/v1/runs/{id}` | GET |
| `mock_gates.json` | embedded in run + gate POST response | GET/POST |
| `mock_lean_canvas.json` | `/v1/runs/{id}/artifacts?kind=lean_canvas` | GET |
| `mock_prd.json` | `/v1/runs/{id}/artifacts?kind=prd` | GET |
| `mock_erd_openapi.json` | `/v1/runs/{id}/artifacts?kind=erd` | GET |
| `mock_review_report.json` | `/v1/runs/{id}/artifacts?kind=review_report` | GET |
| `mock_live_url.json` | `/v1/runs/{id}/artifacts?kind=deploy_url` | GET |
| `mock_launch_kit.json` | `/v1/runs/{id}/artifacts?kind=brand_kit` | GET |
| `mock_llmops_cost.json` | `/v1/llmops/cost` | GET |
| `mock_step_events.json` | WebSocket `/v1/runs/{id}/stream` | WS |
| `mock_cost_ticker.json` | `/v1/llmops/cost` | GET |

---

## Auth requirements summary

| Scope | Endpoints | JWT role |
|-------|-----------|----------|
| Public | `GET /health` | — |
| Founder | All `/v1/*` except admin | `founder` · scopes `runs:read`, `runs:write`, `gates:decide` |
| Admin | `/v1/admin/*` (planned) | `super_admin` |
| Machine | API key via `X-API-Key` (planned) | Service scopes |

**JWT must include:** `sub`, `organization_id`, `role`, `scope`. Tenant context is **never** passed in request body — resolved from token via `OrgContext`.

---

*API inventory v1.0 — June 2026. Save the YAML block above as `openapi.yaml` at repo root when implementing `make api-spec-check`.*
