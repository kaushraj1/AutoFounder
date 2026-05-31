# Database Spec — AutoFounder AI

> PostgreSQL 16 design principles, naming conventions, multi-tenant isolation pattern,
> Redis key schema, and migration rules.

---

## Multi-Tenant Data Model

AutoFounder AI uses a **two-level tenancy hierarchy**:

```
Organization  (billing entity — company or individual subscriber)
  └── Workspace  (project scope — one idea build per workspace)
        └── Run  (a single execution of the 7-pillar pipeline)
```

| Level | Column | Type | Notes |
|-------|--------|------|-------|
| Top-level tenant | `organization_id` | `UUID` | Maps to Auth0 `org_id` claim |
| Project scope | `workspace_id` | `UUID` | Child of `organization_id` |
| Execution | `run_id` | `UUID` | Child of `workspace_id` |

**Every table that holds user data must have `organization_id` as the first non-PK column.**
Tables that are workspace-scoped also carry `workspace_id`.

---

## Tenant Isolation Strategy

### Schema-per-organization (primary isolation)

Each organization gets its own PostgreSQL schema: `org_{organization_id}`.

```sql
-- provisioned automatically when a new organization is created
CREATE SCHEMA org_a1b2c3d4;
SET search_path TO org_a1b2c3d4;
```

Advantages:
- Cross-tenant query is structurally impossible without schema switching.
- `DROP SCHEMA org_x CASCADE` is the complete GDPR right-to-erasure operation.
- No accidental `WHERE` clause omission can leak data.

### Row-Level Security (defense-in-depth)

RLS is applied on every table as a secondary guard. If UDAL search_path is somehow wrong,
RLS catches it at the row level.

```sql
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_isolation ON workspaces
  USING (organization_id = current_setting('app.organization_id')::uuid);
```

The UDAL sets `SET LOCAL app.organization_id = '<id>'` at the start of every transaction.

### What lives in `platform` schema (shared, cross-tenant)

```
platform.organizations       — subscription, tier, status
platform.organization_keys   — hashed API keys
platform.model_registry      — LLM models available, cost/token
platform.prompt_registry     — versioned prompt templates
platform.tool_registry       — MCP tool definitions, rate limits
platform.audit_log           — immutable compliance log (append-only)
```

### What lives in `org_{id}` schema (per-tenant)

```
workspaces          — workspace name, settings, created_by
runs                — pillar pipeline execution state
artifacts           — generated outputs (canvas, ERD, repo URL, etc.)
gates               — HITL gate decisions
step_events         — append-only agent execution log
memory_episodes     — episodic memory per run
cost_ledger         — per-model token billing
```

---

## Naming Conventions

### Tables

- Plural snake_case: `runs`, `step_events`, `memory_episodes`
- Junction tables: `<table_a>_<table_b>` (e.g. `run_artifacts`)
- No abbreviations: `organization_id` not `org_id`, `workspace_id` not `ws_id`

### Columns

| Pattern | Rule | Example |
|---------|------|---------|
| Primary key | `id UUID DEFAULT gen_random_uuid()` | `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` |
| Foreign key | `<table_singular>_id` | `run_id`, `workspace_id` |
| Timestamps | `created_at`, `updated_at`, `deleted_at` | `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` |
| Booleans | Affirmative `is_` or `has_` prefix | `is_active`, `has_mfa` |
| Status enum | `status TEXT` with `CHECK` constraint | `CHECK (status IN ('pending','approved','rejected'))` |
| JSON blobs | `JSONB` not `JSON` | `plan JSONB NOT NULL DEFAULT '{}'` |
| Soft deletes | `deleted_at TIMESTAMPTZ` (nullable) | NULL = active, non-NULL = deleted |

### Indexes

- Name: `idx_<table>_<column(s)>` — e.g. `idx_runs_workspace_id_status`
- Always index foreign keys.
- Always index columns used in `WHERE`, `ORDER BY`, or `JOIN` in hot queries.
- Partial indexes for common filtered queries:
  ```sql
  CREATE INDEX idx_gates_pending ON gates (run_id) WHERE state = 'pending';
  ```

---

## Core Table Schemas

```sql
-- platform.organizations
CREATE TABLE platform.organizations (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name         TEXT NOT NULL,
  slug         TEXT UNIQUE NOT NULL,
  tier         TEXT NOT NULL CHECK (tier IN ('solopreneur','startup','enterprise')),
  status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','deleted')),
  settings     JSONB NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at   TIMESTAMPTZ
);

-- per-org schema: workspaces
CREATE TABLE workspaces (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL,          -- redundant with schema but explicit
  name            TEXT NOT NULL,
  description     TEXT,
  settings        JSONB NOT NULL DEFAULT '{}',
  created_by      TEXT NOT NULL,          -- Auth0 sub claim
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at      TIMESTAMPTZ
);
CREATE INDEX idx_workspaces_organization_id ON workspaces (organization_id);

-- per-org schema: runs
CREATE TABLE runs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL,
  status          TEXT NOT NULL DEFAULT 'queued'
                    CHECK (status IN ('queued','running','paused','completed','failed','cancelled')),
  current_pillar  TEXT,
  plan            JSONB NOT NULL DEFAULT '{}',
  idea_text       TEXT NOT NULL,
  idea_meta       JSONB NOT NULL DEFAULT '{}',
  cost_usd        NUMERIC(12,6) NOT NULL DEFAULT 0,
  created_by      TEXT NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at      TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_runs_workspace_id ON runs (workspace_id);
CREATE INDEX idx_runs_status_created ON runs (status, created_at DESC);

-- per-org schema: gates (HITL checkpoints)
CREATE TABLE gates (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id          UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL,
  kind            TEXT NOT NULL
                    CHECK (kind IN ('validation_approve','architecture_approve',
                                    'infra_spend_approve','launch_approve','canary_rollout')),
  state           TEXT NOT NULL DEFAULT 'pending'
                    CHECK (state IN ('pending','approved','rejected','timed_out')),
  payload         JSONB NOT NULL DEFAULT '{}',
  decided_by      TEXT,
  decided_at      TIMESTAMPTZ,
  timeout_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_gates_run_id_state ON gates (run_id, state);
CREATE INDEX idx_gates_pending ON gates (run_id) WHERE state = 'pending';
```

---

## Migration Rules (Alembic)

1. **Generate**: `uv run alembic revision --autogenerate -m "<imperative description>"`
   e.g. `"add workspace_id to runs"` not `"workspace id"`
2. **Review** the generated file before committing — Alembic autogenerate misses:
   - Partial indexes
   - RLS policies
   - `CHECK` constraints derived from code
   - Custom types
3. **Never** add a bare `NOT NULL` column to a non-empty table. Use a default or make it nullable first.
4. **Always** implement both `upgrade()` and `downgrade()`. Test `downgrade` locally before merge.
5. **Separate migrations** for `platform` schema changes vs per-tenant schema changes.
6. Migration file is committed in the same PR as the application code that depends on it.
7. CI runs `alembic upgrade head` from a clean Docker volume on every PR.

---

## Redis Key Schema

All Redis keys are prefixed with `{organization_id}:` to enforce tenant isolation at the cache layer.

| Key pattern | Type | TTL | Purpose |
|-------------|------|-----|---------|
| `{org_id}:orch:checkpoint:{run_id}` | Hash | 24h | LangGraph hot checkpoint |
| `{org_id}:agent:session:{run_id}:{agent_id}` | Hash | 24h | Agent working state |
| `{org_id}:llm:cache:{sha256_prompt}` | String (JSON) | 1h | Semantic prompt cache |
| `{org_id}:embed:cache:{sha256_text}:{model}` | String (JSON) | 24h | Embedding cache |
| `{org_id}:gate:pending:{run_id}` | String | 4h | Quick gate existence check |
| `{org_id}:cost:{YYYY-MM}` | Hash | EOM+7d | Monthly cost accumulator |
| `ratelimit:{org_id}:{route}:{minute_bucket}` | String (int) | 120s | Per-org rate limit counter |
| `queue:tasks:{pillar}` | Sorted Set | — | Priority task queue (score = priority) |

**Rules**:
- Never store PII in Redis.
- Never store secrets in Redis.
- Every key that holds tenant data must be prefixed with `{organization_id}:`.
- TTL must be set on every key — no unbounded keys.

---

## Observability

- Every migration run emits a structured log: `{"event": "migration", "revision": "...", "duration_ms": ...}`
<<<<<<< HEAD
- Slow queries (> 200 ms) are logged at `WARN` level. `pg_stat_statements` is enabled in Cloud SQL.
=======
- Slow queries (> 200 ms) are logged at `WARN` level. `pg_stat_statements` is enabled in Supabase/PostgreSQL.
>>>>>>> dev
- Connection pool metrics (active, idle, wait) are exported to Prometheus via the UDAL layer.
