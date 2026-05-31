# API Design Spec — AutoFounder AI

> REST conventions, authentication, response shapes, error format,
> pagination, rate limiting, and versioning rules for all FastAPI routes.

---

## Base URL & Versioning

```
Production:  https://api.autofounder.ai/v1
Staging:     https://api-staging.autofounder.ai/v1
Local:       http://localhost:8000/v1
```

- Version is a URL path prefix: `/v1/`, `/v2/`, etc.
- A breaking change (removed field, changed type, renamed param) **must** bump the version.
- Non-breaking additions (new optional field, new endpoint) do not require a version bump.
- `/v1/` is supported indefinitely once released. Sunset is announced 6 months in advance.
- Internal agent-to-agent calls use gRPC (not REST). This spec covers the public/frontend REST surface only.

---

## Authentication

### Human users (Founder Portal, Admin, Mobile, VS Code Extension)

```
<<<<<<< HEAD
Authorization: Bearer <Auth0 JWT>
```

- JWTs are short-lived (15 min). Frontend refreshes silently using the refresh token.
- Every JWT must contain: `sub` (user ID), `org` (organization_id), `role`, `scopes`.
- MFA is enforced for all human accounts via Auth0.
=======
Authorization: Bearer <Supabase JWT>
```

- JWTs are short-lived (15 min). Frontend refreshes silently via the Supabase Auth client.
- Every JWT must contain: `sub` (user ID), `tenant_id` (tenant ID), `role`, `scopes`.
- MFA is enforced for all human accounts via Supabase Auth.
>>>>>>> dev

### Machine clients (API keys)

```
X-API-Key: af_<base64url_random_32_bytes>
```

- Keys are stored as bcrypt hashes in `platform.organization_keys` — never in plaintext.
- Key rotation: `POST /v1/organizations/{id}/keys` — generates a new key and revokes the old one after 24 h grace.
- Scopes are checked the same way as JWT scopes.

### Extracting tenant context

Every route handler receives `organization_id` and `workspace_id` from the resolved auth context —
never from the request body or query string. The FastAPI dependency chain:

```
verify_token() → resolve_org() → inject OrgContext → route handler
```

The UDAL is called with this context. Passing `organization_id` directly to UDAL from business logic
is **forbidden** — it must flow through the auth dependency.

---

## Response Envelope

All responses use a consistent JSON wrapper:

### Success

```json
{
  "data": { ... },
  "meta": {
    "request_id": "af-req-01j...",
    "timestamp": "2026-05-20T10:00:00Z"
  }
}
```

### Paginated success

```json
{
  "data": [ ... ],
  "pagination": {
    "cursor": "eyJpZCI6Inh4eHgifQ==",
    "has_more": true,
    "total": 142
  },
  "meta": {
    "request_id": "af-req-01j...",
    "timestamp": "2026-05-20T10:00:00Z"
  }
}
```

### Error

```json
{
  "error": {
    "code": "AF_ERR_GATE_ALREADY_DECIDED",
    "message": "Gate g-01j... has already been decided.",
    "details": { "gate_id": "g-01j...", "current_state": "approved" }
  },
  "meta": {
    "request_id": "af-req-01j...",
    "timestamp": "2026-05-20T10:00:00Z"
  }
}
```

**Rules**:
- `data` is always an object (single resource) or array (collection) — never a primitive.
- `error.code` is always a namespaced SCREAMING_SNAKE_CASE string prefixed with `AF_ERR_`.
- `error.message` is human-readable, safe to display in UI.
- `error.details` is optional; provides machine-readable context for the client.
- Never include stack traces, SQL, or internal paths in error responses.

---

## Error Codes

| HTTP Status | `error.code` | Meaning |
|-------------|--------------|---------|
| 400 | `AF_ERR_VALIDATION` | Request body/param failed Pydantic validation |
| 401 | `AF_ERR_UNAUTHORIZED` | Missing or invalid token |
| 403 | `AF_ERR_FORBIDDEN` | Token valid but insufficient scope |
| 404 | `AF_ERR_NOT_FOUND` | Resource does not exist (or belongs to another org) |
| 409 | `AF_ERR_CONFLICT` | State conflict (e.g. gate already decided) |
| 402 | `AF_ERR_COST_CAP_EXCEEDED` | Org has hit monthly cost limit |
| 429 | `AF_ERR_RATE_LIMITED` | Too many requests |
| 422 | `AF_ERR_UNPROCESSABLE` | Business-logic validation failed (beyond Pydantic) |
| 500 | `AF_ERR_INTERNAL` | Unexpected server error |
| 503 | `AF_ERR_UNAVAILABLE` | Dependency (LLM, DB) temporarily unavailable |

---

## Core Endpoints

```
POST   /v1/ideas                              Submit new idea → run_id
GET    /v1/runs/{run_id}                      Run state, active gates, artifacts
POST   /v1/runs/{run_id}/gates/{gate_id}      Approve / reject HITL gate
GET    /v1/runs/{run_id}/artifacts            List generated artifacts
GET    /v1/runs/{run_id}/stream               WebSocket upgrade — live step events
DELETE /v1/runs/{run_id}                      Cancel a run

GET    /v1/workspaces                         List workspaces for current org
POST   /v1/workspaces                         Create workspace
GET    /v1/workspaces/{workspace_id}/runs     List runs in a workspace

POST   /v1/feedback                           Accept/reject signal for LLMOps RLHF
GET    /v1/llmops/cost                        Per-org cost telemetry

POST   /v1/organizations/{id}/keys            Rotate API key
DELETE /v1/organizations/{id}/keys/{key_id}  Revoke a key
```

---

## Pagination

Use **cursor-based pagination** for all list endpoints. Offset pagination is forbidden (breaks under
concurrent inserts and doesn't scale).

### Request

```
GET /v1/workspaces/{id}/runs?limit=25&cursor=eyJpZCI6Inh4eHgifQ==&order=desc
```

| Param | Default | Max | Notes |
|-------|---------|-----|-------|
| `limit` | 25 | 100 | Items per page |
| `cursor` | — | — | Opaque base64url token from previous response |
| `order` | `desc` | `asc` or `desc` | Ordered by `created_at` |

### Cursor encoding

The cursor encodes the last-seen row's sort key(s). It is opaque to the client.

```python
import base64, json

def encode_cursor(run_id: str, created_at: str) -> str:
    payload = json.dumps({"id": run_id, "ca": created_at})
    return base64.urlsafe_b64encode(payload.encode()).decode()

def decode_cursor(cursor: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(cursor))
```

---

## Rate Limiting

Rate limits are enforced per organization per route group, tracked in Redis.

| Tier | Limit | Window |
|------|-------|--------|
| Solopreneur | 30 requests | 1 minute |
| Startup | 120 requests | 1 minute |
| Enterprise | 600 requests | 1 minute |

When exceeded, respond with `429` and include:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 42
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1748000042
```

`POST /v1/ideas` has a separate, stricter limit (1 active run per Solopreneur org, 5 for Startup)
enforced at the business logic layer, not the rate limiter.

---

## WebSocket — Live Run Stream

Upgrade path: `GET /v1/runs/{run_id}/stream` with `Upgrade: websocket`.

### Server → Client frame format

```json
{ "type": "step.started",   "step_id": "...", "agent_id": "...", "at": "ISO8601" }
{ "type": "token",          "content": "...", "step_id": "..." }
{ "type": "tool.call",      "tool": "...", "args": {}, "step_id": "..." }
{ "type": "step.completed", "step_id": "...", "at": "ISO8601" }
{ "type": "gate.required",  "gate_id": "...", "kind": "...", "payload": {} }
{ "type": "run.completed",  "run_id": "...", "cost_usd": 0.42 }
{ "type": "run.failed",     "run_id": "...", "error": "..." }
```

### Client → Server

```json
{ "type": "ping" }
```

Gate decisions are made via `POST /v1/runs/{run_id}/gates/{gate_id}` (REST), not WebSocket.

### Reconnection

Client sends `Last-Event-ID: <step_id>` header on reconnect. Server replays `step_events` from
that point forward. Replay window: 30 minutes.

---

## OpenAPI Contract

- Every route has a corresponding entry in `openapi.yaml` at the repo root.
- Fields: `operationId` (camelCase unique), `summary` (≤ 80 chars), `tags`, `security`,
  `requestBody`, `responses` (200/201/4xx/500 documented).
- CI runs `make api-spec-check` which diffs `openapi.yaml` against the live FastAPI schema.
  The PR fails if they diverge.
- Breaking changes to `v1` are forbidden. Introduce `v2/` instead.

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| URL path segments | kebab-case, plural resources | `/v1/runs`, `/v1/run-artifacts` |
| Path params | snake_case | `{run_id}`, `{gate_id}` |
| Query params | snake_case | `?workspace_id=...&has_more=true` |
| JSON body keys | snake_case | `{"idea_text": "..."}` |
| `operationId` | camelCase | `createRun`, `decideGate` |
| Error codes | SCREAMING_SNAKE_CASE | `AF_ERR_NOT_FOUND` |
