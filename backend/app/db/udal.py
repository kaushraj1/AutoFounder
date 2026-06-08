"""Unified Data Access Layer (UDAL).

Single façade over all storage backends.  Every agent and service that needs
data goes through UDAL so that:
  - Tenant scoping (organization_id) cannot be bypassed.
  - Every access is visible in the lineage audit log.
  - Cross-tenant breaches are caught at SEV-1 severity before any query runs.

Construction:
    udal = UDAL(principal, session)   # sets ContextVar immediately

Accessors:
    async with udal.relational() as db:   # SET LOCAL search_path + RLS param
        rows = await db.session.execute(...)

    vec = udal.vector()                   # shares same session + search_path
    obj = udal.object()                   # Supabase Storage, tenant-prefixed
    udal.graph()                          # NotImplementedError — open decision

SEV-1 cross-tenant guard:
    If any code mutates the ContextVar to a different org_id after UDAL is
    constructed, _guard() raises CrossTenantViolation before a query can run.
    This is defense-in-depth on top of the schema-level and RLS isolation.
"""

from __future__ import annotations

import logging

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal
from app.db.cache import CacheClient
from app.db.context import get_tenant_context, set_tenant_context
from app.db.graph import GraphClient
from app.db.object_store import ObjectClient
from app.db.relational import RelationalClient
from app.db.vector import VectorClient

logger = logging.getLogger(__name__)


class CrossTenantViolation(RuntimeError):
    """SEV-1: UDAL principal org_id ≠ ContextVar org_id.

    Raised before any query is executed.  The caller must treat this as a
    hard stop — do not catch and continue.  Emit an alert, abort the request.
    """


class UDAL:
    """Tenant-scoped façade over PostgreSQL, pgvector, graph DB, and object store."""

    def __init__(
        self,
        principal: Principal,
        session: AsyncSession,
        redis: aioredis.Redis | None = None,
    ) -> None:
        self._principal = principal
        self._session = session
        self._redis = redis
        set_tenant_context(principal.organization_id)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _guard(self) -> None:
        """Cross-tenant guard — SEV-1 on breach.

        Compares the ContextVar (set at construction) against this UDAL
        instance's principal.  A mismatch means the ContextVar was overwritten
        by another concurrent UDAL in the same asyncio Task — that is a
        cross-tenant data breach.
        """
        ctx = get_tenant_context()
        if ctx is not None and ctx != self._principal.organization_id:
            msg = (
                f"SEV-1 CROSS-TENANT BREACH — "
                f"UDAL principal={self._principal.organization_id!r} "
                f"context={ctx!r}"
            )
            logger.critical(msg)
            raise CrossTenantViolation(msg)

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    @property
    def organization_id(self) -> str:
        return self._principal.organization_id

    def relational(self) -> RelationalClient:
        """Async context manager: tenant-scoped SQLAlchemy session.

        Sets search_path and app.organization_id for the transaction.
        """
        self._guard()
        return RelationalClient(
            org_id=self._principal.organization_id,
            session=self._session,
            actor=self._principal.role,
        )

    def vector(self) -> VectorClient:
        """pgvector search/upsert on the tenant's memory_episodes table.

        Reuses the same session — call after entering relational() context
        so search_path is already set.
        """
        self._guard()
        return VectorClient(
            org_id=self._principal.organization_id,
            session=self._session,
        )

    def graph(self) -> GraphClient:
        """Graph DB client — always raises NotImplementedError (open decision).

        See .claude/specs/stack.md § Open Decisions.
        """
        return GraphClient()

    def object(self) -> ObjectClient:
        """Supabase Storage client scoped to this tenant.

        All paths are prefixed with org_{org_id}/.
        Requires the 'data' dependency group: uv sync --group data.
        """
        self._guard()
        return ObjectClient(org_id=self._principal.organization_id)

    def cache(self) -> CacheClient:
        """Tenant-scoped Redis cache client.

        Raises RuntimeError if UDAL was constructed without a Redis client.
        All keys are prefixed org:{org_id}: — cross-tenant access is impossible.
        """
        if self._redis is None:
            raise RuntimeError(
                "UDAL constructed without Redis — pass redis=get_redis() to enable cache()."
            )
        self._guard()
        return CacheClient(org_id=self._principal.organization_id, redis=self._redis)
