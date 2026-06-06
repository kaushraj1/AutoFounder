"""per-tenant schema provisioner (workspaces, runs, artifacts, gates, step_events,
memory_episodes, cost_ledger) + orchestrator.checkpoints for LangGraph

Revision ID: 0003_tenant_schema
Revises: 0002_platform_schema
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_tenant_schema"
down_revision: str | None = "0002_platform_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pgvector is optional in some environments (e.g., plain Postgres in CI).
    # Try to install when available; otherwise continue with array-based fallback.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_available_extensions
                WHERE name = 'vector'
            ) THEN
                BEGIN
                    CREATE EXTENSION IF NOT EXISTS vector;
                EXCEPTION
                    WHEN insufficient_privilege THEN
                        RAISE NOTICE 'Skipping CREATE EXTENSION vector (insufficient privileges)';
                END;
            ELSE
                RAISE NOTICE 'pgvector extension is not available; using fallback schema';
            END IF;
        END
        $$;
    """)

    # ------------------------------------------------------------------
    # orchestrator schema — LangGraph checkpoint persistence
    # ------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS orchestrator")

    op.execute("""
        CREATE TABLE IF NOT EXISTS orchestrator.checkpoints (
            run_id                  UUID        NOT NULL,
            checkpoint_ns           TEXT        NOT NULL DEFAULT '',
            checkpoint_id           TEXT        NOT NULL,
            parent_checkpoint_id    TEXT,
            type                    TEXT,
            checkpoint              JSONB       NOT NULL DEFAULT '{}',
            metadata                JSONB       NOT NULL DEFAULT '{}',
            created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (run_id, checkpoint_ns, checkpoint_id)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_checkpoints_run_id ON orchestrator.checkpoints (run_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_checkpoints_run_id_created "
        "ON orchestrator.checkpoints (run_id, created_at DESC)"
    )

    # ------------------------------------------------------------------
    # provision_org_schema(org_id TEXT)
    # Called once per new organization at signup via UDAL.
    # Creates schema org_{org_id} with all 7 per-tenant tables,
    # RLS policies, indexes, and the step_events Realtime trigger.
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION provision_org_schema(org_id TEXT)
        RETURNS void
        LANGUAGE plpgsql
        AS $$
        DECLARE
            s TEXT := format('org_%s', org_id);
            has_vector BOOLEAN := false;
        BEGIN

            -- Detect whether pgvector is installed in this database at runtime.
            SELECT EXISTS (
                SELECT 1
                FROM pg_extension
                WHERE extname = 'vector'
            ) INTO has_vector;

            -- schema
            EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', s);

            -- --------------------------------------------------------
            -- workspaces
            -- --------------------------------------------------------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %I.workspaces (
                    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                    organization_id UUID        NOT NULL,
                    name            TEXT        NOT NULL,
                    description     TEXT,
                    settings        JSONB       NOT NULL DEFAULT '{}',
                    created_by      TEXT        NOT NULL,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
                    deleted_at      TIMESTAMPTZ
                )
            $sql$, s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_workspaces_organization_id '
                'ON %I.workspaces (organization_id)', s);
            EXECUTE format('ALTER TABLE %I.workspaces ENABLE ROW LEVEL SECURITY', s);
            EXECUTE format($sql$
                CREATE POLICY org_isolation ON %I.workspaces
                    USING (organization_id = current_setting('app.organization_id', true)::uuid)
            $sql$, s);

            -- --------------------------------------------------------
            -- runs
            -- --------------------------------------------------------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %I.runs (
                    id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
                    workspace_id    UUID          NOT NULL REFERENCES
                                                  %I.workspaces(id) ON DELETE CASCADE,
                    organization_id UUID          NOT NULL,
                    status          TEXT          NOT NULL DEFAULT 'queued'
                                                  CHECK (status IN (
                                                      'queued','running','paused',
                                                      'completed','failed','cancelled')),
                    current_pillar  TEXT,
                    plan            JSONB         NOT NULL DEFAULT '{}',
                    idea_text       TEXT          NOT NULL,
                    idea_meta       JSONB         NOT NULL DEFAULT '{}',
                    cost_usd        NUMERIC(12,6) NOT NULL DEFAULT 0,
                    created_by      TEXT          NOT NULL,
                    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
                    started_at      TIMESTAMPTZ,
                    completed_at    TIMESTAMPTZ
                )
            $sql$, s, s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_runs_workspace_id '
                'ON %I.runs (workspace_id)', s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_runs_status_created '
                'ON %I.runs (status, created_at DESC)', s);
            EXECUTE format('ALTER TABLE %I.runs ENABLE ROW LEVEL SECURITY', s);
            EXECUTE format($sql$
                CREATE POLICY org_isolation ON %I.runs
                    USING (organization_id = current_setting('app.organization_id', true)::uuid)
            $sql$, s);

            -- --------------------------------------------------------
            -- artifacts
            -- --------------------------------------------------------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %I.artifacts (
                    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                    run_id          UUID        NOT NULL REFERENCES %I.runs(id) ON DELETE CASCADE,
                    organization_id UUID        NOT NULL,
                    kind            TEXT        NOT NULL CHECK (kind IN (
                                                    'lean_canvas','erd','openapi_spec','repo_url',
                                                    'brand_kit','landing_page','social_posts',
                                                    'email_sequences','deploy_url',
                                                    'test_report','llmops_report')),
                    content_url     TEXT,
                    content         JSONB       NOT NULL DEFAULT '{}',
                    metadata        JSONB       NOT NULL DEFAULT '{}',
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            $sql$, s, s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_artifacts_run_id '
                'ON %I.artifacts (run_id)', s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_artifacts_run_id_kind '
                'ON %I.artifacts (run_id, kind)', s);
            EXECUTE format('ALTER TABLE %I.artifacts ENABLE ROW LEVEL SECURITY', s);
            EXECUTE format($sql$
                CREATE POLICY org_isolation ON %I.artifacts
                    USING (organization_id = current_setting('app.organization_id', true)::uuid)
            $sql$, s);

            -- --------------------------------------------------------
            -- gates (HITL checkpoints)
            -- --------------------------------------------------------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %I.gates (
                    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                    run_id          UUID        NOT NULL REFERENCES %I.runs(id) ON DELETE CASCADE,
                    organization_id UUID        NOT NULL,
                    kind            TEXT        NOT NULL CHECK (kind IN (
                                                    'validation_approve','architecture_approve',
                                                    'infra_spend_approve','launch_approve',
                                                    'canary_rollout')),
                    state           TEXT        NOT NULL DEFAULT 'pending'
                                                CHECK (state IN (
                                                    'pending','approved','rejected','timed_out')),
                    payload         JSONB       NOT NULL DEFAULT '{}',
                    decided_by      TEXT,
                    decided_at      TIMESTAMPTZ,
                    timeout_at      TIMESTAMPTZ,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            $sql$, s, s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_gates_run_id_state '
                'ON %I.gates (run_id, state)', s);
            -- partial index: pending gates only (hot path for gate polling)
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_gates_pending '
                'ON %I.gates (run_id) WHERE state = ''pending''', s);
            EXECUTE format('ALTER TABLE %I.gates ENABLE ROW LEVEL SECURITY', s);
            EXECUTE format($sql$
                CREATE POLICY org_isolation ON %I.gates
                    USING (organization_id = current_setting('app.organization_id', true)::uuid)
            $sql$, s);

            -- --------------------------------------------------------
            -- step_events (append-only agent execution log)
            -- --------------------------------------------------------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %I.step_events (
                    id              BIGINT      PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    run_id          UUID        NOT NULL REFERENCES %I.runs(id) ON DELETE CASCADE,
                    organization_id UUID        NOT NULL,
                    pillar          TEXT        NOT NULL,
                    agent_id        TEXT        NOT NULL,
                    event_type      TEXT        NOT NULL CHECK (event_type IN (
                                                    'started','progress','completed',
                                                    'failed','gate_required')),
                    payload         JSONB       NOT NULL DEFAULT '{}',
                    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            $sql$, s, s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_step_events_run_id '
                'ON %I.step_events (run_id)', s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_step_events_run_id_pillar '
                'ON %I.step_events (run_id, pillar)', s);
            EXECUTE format('ALTER TABLE %I.step_events ENABLE ROW LEVEL SECURITY', s);
            EXECUTE format($sql$
                CREATE POLICY org_isolation ON %I.step_events
                    USING (organization_id = current_setting('app.organization_id', true)::uuid)
            $sql$, s);
            -- append-only: block UPDATE and DELETE at the rule level
            EXECUTE format($sql$
                CREATE RULE step_events_no_update AS
                    ON UPDATE TO %I.step_events DO INSTEAD NOTHING
            $sql$, s);
            EXECUTE format($sql$
                CREATE RULE step_events_no_delete AS
                    ON DELETE TO %I.step_events DO INSTEAD NOTHING
            $sql$, s);
            -- pg_notify trigger feeds Supabase Realtime (AF-031)
            EXECUTE format($sql$
                CREATE OR REPLACE FUNCTION %I.notify_step_event()
                RETURNS trigger LANGUAGE plpgsql AS $fn$
                BEGIN
                    PERFORM pg_notify('step_events', row_to_json(NEW)::text);
                    RETURN NEW;
                END;
                $fn$
            $sql$, s);
            EXECUTE format($sql$
                CREATE TRIGGER step_event_notify
                    AFTER INSERT ON %I.step_events
                    FOR EACH ROW EXECUTE FUNCTION %I.notify_step_event()
            $sql$, s, s);

            -- --------------------------------------------------------
            -- memory_episodes (episodic agent memory + pgvector)
            -- --------------------------------------------------------
            IF has_vector THEN
                EXECUTE format($sql$
                    CREATE TABLE IF NOT EXISTS %I.memory_episodes (
                        id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                        run_id          UUID        NOT NULL REFERENCES
                                                  %I.runs(id) ON DELETE CASCADE,
                        organization_id UUID        NOT NULL,
                        agent_id        TEXT        NOT NULL,
                        role            TEXT        NOT NULL CHECK (role IN (
                                                        'user','assistant','tool','system')),
                        content         TEXT        NOT NULL,
                        embedding       vector(768),
                        metadata        JSONB       NOT NULL DEFAULT '{}',
                        created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                $sql$, s, s);
            ELSE
                -- Fallback type keeps migrations portable when pgvector is unavailable.
                EXECUTE format($sql$
                    CREATE TABLE IF NOT EXISTS %I.memory_episodes (
                        id              UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
                        run_id          UUID             NOT NULL REFERENCES
                                                      %I.runs(id) ON DELETE CASCADE,
                        organization_id UUID             NOT NULL,
                        agent_id        TEXT             NOT NULL,
                        role            TEXT             NOT NULL CHECK (role IN (
                                                        'user','assistant','tool','system')),
                        content         TEXT             NOT NULL,
                        embedding       DOUBLE PRECISION[],
                        metadata        JSONB            NOT NULL DEFAULT '{}',
                        created_at      TIMESTAMPTZ      NOT NULL DEFAULT now()
                    )
                $sql$, s, s);
            END IF;
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_memory_episodes_run_id '
                'ON %I.memory_episodes (run_id)', s);
            -- IVFFlat ANN index for hybrid BM25+ANN retrieval (AF-049)
            IF has_vector THEN
                EXECUTE format($sql$
                    CREATE INDEX IF NOT EXISTS idx_memory_episodes_embedding
                        ON %I.memory_episodes USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100)
                $sql$, s);
            END IF;
            EXECUTE format('ALTER TABLE %I.memory_episodes ENABLE ROW LEVEL SECURITY', s);
            EXECUTE format($sql$
                CREATE POLICY org_isolation ON %I.memory_episodes
                    USING (organization_id = current_setting('app.organization_id', true)::uuid)
            $sql$, s);

            -- --------------------------------------------------------
            -- cost_ledger (per-model token billing)
            -- --------------------------------------------------------
            EXECUTE format($sql$
                CREATE TABLE IF NOT EXISTS %I.cost_ledger (
                    id              BIGINT        PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    run_id          UUID          NOT NULL REFERENCES %I.runs(id) ON DELETE CASCADE,
                    organization_id UUID          NOT NULL,
                    model_id        TEXT          NOT NULL,
                    input_tokens    INTEGER       NOT NULL DEFAULT 0,
                    output_tokens   INTEGER       NOT NULL DEFAULT 0,
                    cost_usd        NUMERIC(12,6) NOT NULL DEFAULT 0,
                    recorded_at     TIMESTAMPTZ   NOT NULL DEFAULT now()
                )
            $sql$, s, s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_cost_ledger_run_id '
                'ON %I.cost_ledger (run_id)', s);
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS idx_cost_ledger_recorded_at '
                'ON %I.cost_ledger (recorded_at DESC)', s);
            EXECUTE format('ALTER TABLE %I.cost_ledger ENABLE ROW LEVEL SECURITY', s);
            EXECUTE format($sql$
                CREATE POLICY org_isolation ON %I.cost_ledger
                    USING (organization_id = current_setting('app.organization_id', true)::uuid)
            $sql$, s);

        END;
        $$
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS provision_org_schema(TEXT)")
    op.execute("DROP TABLE IF EXISTS orchestrator.checkpoints")
    op.execute("DROP SCHEMA IF EXISTS orchestrator")
