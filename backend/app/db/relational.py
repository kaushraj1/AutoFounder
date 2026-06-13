"""Tenant-scoped relational (PostgreSQL) client.

Usage:
    async with udal.relational() as db:
        result = await db.session.execute(select(Run).where(...))
        await db.audit("read", "runs", str(run_id))

On __aenter__ the client sets two transaction-local Postgres session variables:
- search_path  — routes unqualified table names to the right tenant schema
- app.organization_id — read by RLS policies on every table as defense-in-depth

Both use SET LOCAL so they are scoped to the current transaction and cannot
bleed across connection pool reuse.
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.audit import emit_audit_event


class RelationalClient:
    """Async context manager wrapping an AsyncSession with tenant isolation."""

    def __init__(self, org_id: str, session: AsyncSession, actor: str) -> None:
        self._org_id = org_id
        self._session = session
        self._actor = actor

    async def __aenter__(self) -> Self:
        schema = f'"org_{self._org_id}"'
        await self._session.execute(text(f"SET LOCAL search_path TO {schema}, platform, public;"))
        await self._session.execute(text(f"SET LOCAL app.organization_id = '{self._org_id}';"))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def audit(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        *,
        run_id: str | None = None,
        agent_id: str | None = None,
        outcome: str = "success",
        metadata: dict | None = None,
    ) -> None:
        await emit_audit_event(
            self._session,
            org_id=self._org_id,
            actor=self._actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            run_id=run_id,
            agent_id=agent_id,
            outcome=outcome,
            metadata=metadata,
        )
