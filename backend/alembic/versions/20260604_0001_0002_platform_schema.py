"""platform schema: tenants, model_registry, prompt_registry, tool_registry, audit_log, tenant_api_keys

Revision ID: 0002_platform_schema
Revises: 0001_initial
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_platform_schema"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS platform")

    # ------------------------------------------------------------------
    # platform.tenants — billing/subscription entity per organization
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform.tenants (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            name        TEXT        NOT NULL,
            slug        TEXT        UNIQUE NOT NULL,
            tier        TEXT        NOT NULL CHECK (tier IN ('solopreneur', 'startup', 'enterprise')),
            status      TEXT        NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active', 'suspended', 'deleted')),
            settings    JSONB       NOT NULL DEFAULT '{}',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at  TIMESTAMPTZ
        )
    """)
    op.execute("ALTER TABLE platform.tenants ENABLE ROW LEVEL SECURITY")

    # ------------------------------------------------------------------
    # platform.tenant_api_keys — hashed API keys per tenant
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform.tenant_api_keys (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID        NOT NULL REFERENCES platform.tenants(id) ON DELETE CASCADE,
            key_hash    TEXT        NOT NULL,
            label       TEXT,
            scopes      TEXT[]      NOT NULL DEFAULT '{}',
            expires_at  TIMESTAMPTZ,
            revoked_at  TIMESTAMPTZ,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_tenant_api_keys_tenant_id ON platform.tenant_api_keys (tenant_id)")
    op.execute("ALTER TABLE platform.tenant_api_keys ENABLE ROW LEVEL SECURITY")

    # ------------------------------------------------------------------
    # platform.model_registry — available LLM models, routing config
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform.model_registry (
            id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            model_id                    TEXT        UNIQUE NOT NULL,
            provider                    TEXT        NOT NULL,
            version                     TEXT        NOT NULL,
            task_classes                TEXT[]      NOT NULL DEFAULT '{}',
            cost_per_1k_input_tokens    NUMERIC(12, 8) NOT NULL DEFAULT 0,
            cost_per_1k_output_tokens   NUMERIC(12, 8) NOT NULL DEFAULT 0,
            eval_scores                 JSONB       NOT NULL DEFAULT '{}',
            is_active                   BOOLEAN     NOT NULL DEFAULT true,
            rollback_to                 UUID        REFERENCES platform.model_registry(id),
            registered_at               TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_model_registry_is_active ON platform.model_registry (is_active)")
    op.execute("ALTER TABLE platform.model_registry ENABLE ROW LEVEL SECURITY")

    # ------------------------------------------------------------------
    # platform.prompt_registry — versioned Jinja2 prompt templates
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform.prompt_registry (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            name        TEXT        NOT NULL,
            version     TEXT        NOT NULL,
            agent       TEXT        NOT NULL,
            template_s3 TEXT        NOT NULL,
            variables   JSONB       NOT NULL DEFAULT '{}',
            status      TEXT        NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active', 'canary', 'retired')),
            eval_score  NUMERIC(5, 4),
            created_by  TEXT        NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (name, version)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_prompt_registry_agent_status ON platform.prompt_registry (agent, status)")
    op.execute("ALTER TABLE platform.prompt_registry ENABLE ROW LEVEL SECURITY")

    # ------------------------------------------------------------------
    # platform.tool_registry — MCP tool definitions and rate limits
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform.tool_registry (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            name        TEXT        UNIQUE NOT NULL,
            description TEXT        NOT NULL,
            args_schema JSONB       NOT NULL DEFAULT '{}',
            auth_scope  TEXT        NOT NULL,
            cost_class  TEXT        NOT NULL CHECK (cost_class IN ('free', 'cheap', 'expensive')),
            rate_limit  JSONB       NOT NULL DEFAULT '{}',
            is_active   BOOLEAN     NOT NULL DEFAULT true
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_tool_registry_is_active ON platform.tool_registry (is_active)")
    op.execute("ALTER TABLE platform.tool_registry ENABLE ROW LEVEL SECURITY")

    # ------------------------------------------------------------------
    # platform.audit_log — immutable compliance trail (append-only)
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform.audit_log (
            id              BIGINT      PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            tenant_id       UUID        REFERENCES platform.tenants(id),
            run_id          UUID,
            agent_id        TEXT,
            action          TEXT        NOT NULL,
            resource_type   TEXT        NOT NULL,
            resource_id     TEXT,
            actor           TEXT        NOT NULL,
            outcome         TEXT        NOT NULL CHECK (outcome IN ('success', 'failure', 'blocked')),
            metadata        JSONB,
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_tenant_id ON platform.audit_log (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_occurred_at ON platform.audit_log (occurred_at DESC)")
    op.execute("ALTER TABLE platform.audit_log ENABLE ROW LEVEL SECURITY")

    # Prevent updates and deletes on audit_log — it is append-only
    op.execute("""
        CREATE OR REPLACE RULE audit_log_no_update AS
            ON UPDATE TO platform.audit_log DO INSTEAD NOTHING
    """)
    op.execute("""
        CREATE OR REPLACE RULE audit_log_no_delete AS
            ON DELETE TO platform.audit_log DO INSTEAD NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP RULE IF EXISTS audit_log_no_delete ON platform.audit_log")
    op.execute("DROP RULE IF EXISTS audit_log_no_update ON platform.audit_log")
    op.execute("DROP TABLE IF EXISTS platform.audit_log")
    op.execute("DROP TABLE IF EXISTS platform.tool_registry")
    op.execute("DROP TABLE IF EXISTS platform.prompt_registry")
    op.execute("DROP TABLE IF EXISTS platform.model_registry")
    op.execute("DROP TABLE IF EXISTS platform.tenant_api_keys")
    op.execute("DROP TABLE IF EXISTS platform.tenants")
    op.execute("DROP SCHEMA IF EXISTS platform")
