"""Unified Data Access Layer (UDAL) — see CLAUDE.md §19.2.

Every agent/service data access MUST go through the UDAL so that tenant scoping
(``organization_id``) cannot be bypassed and each access can emit a lineage event.
Phase 1 defines the surface; Sprint 1 implements relational/vector/graph/object routing.
"""

from app.core.security import Principal


class UDAL:
    """Tenant-scoped facade over all data stores."""

    def __init__(self, principal: Principal) -> None:
        self._principal = principal

    @property
    def organization_id(self) -> str:
        """The tenant every query is scoped to."""
        return self._principal.organization_id

    def relational(self) -> object:
        """Tenant-scoped relational (PostgreSQL) access."""
        raise NotImplementedError("UDAL.relational lands in Phase 1 Sprint 1")

    def vector(self) -> object:
        """Tenant-scoped vector (pgvector) access."""
        raise NotImplementedError("UDAL.vector lands in Phase 1 Sprint 1")
