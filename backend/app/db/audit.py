"""Lineage audit emit — writes to platform.audit_log.

Every UDAL data access that touches tenant data calls emit_audit_event.
The table is append-only (UPDATE/DELETE rules block both operations in the DB).
Failures are swallowed and logged so a broken audit path never blocks the
actual operation — the audit is defense-in-depth, not a gate.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def emit_audit_event(
    session: AsyncSession,
    *,
    org_id: str,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    run_id: str | None = None,
    agent_id: str | None = None,
    outcome: str = "success",
    metadata: dict | None = None,
) -> None:
    """Insert one row into platform.audit_log.

    Parameters match the audit_log schema (migration 0002_platform_schema).
    Outcome must be 'success' | 'failure' | 'blocked'.
    """
    try:
        await session.execute(
            text("""
                INSERT INTO platform.audit_log
                    (tenant_id, run_id, agent_id, action, resource_type,
                     resource_id, actor, outcome, metadata)
                SELECT
                    t.id,
                    CAST(:run_id AS UUID),
                    :agent_id,
                    :action,
                    :resource_type,
                    :resource_id,
                    :actor,
                    :outcome,
                    CAST(:metadata AS JSONB)
                FROM platform.tenants t
                WHERE t.slug = :org_id
                LIMIT 1
            """),
            {
                "run_id": run_id,
                "agent_id": agent_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "actor": actor,
                "outcome": outcome,
                "metadata": (__import__("json").dumps(metadata) if metadata else "{}"),
                "org_id": org_id,
            },
        )
    except Exception:
        logger.exception(
            "audit_emit_failed org=%s action=%s resource_type=%s",
            org_id,
            action,
            resource_type,
        )
