"""Authentication / authorization helpers.

Phase 1 ships a permissive development principal so local flows work end-to-end without
a real identity provider. Sprint 1 replaces ``verify_jwt`` with Supabase JWT verification:
validate the signature with ``SUPABASE_JWT_SECRET`` and extract ``organization_id`` / ``role`` /
``scopes`` claims, which then flow into the Unified Data Access Layer for tenant scoping.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    """The authenticated caller. ``organization_id`` drives all tenant isolation."""

    organization_id: str
    role: str = "founder"


# Fixed principal used in development until real auth lands.
DEV_PRINCIPAL = Principal(organization_id="org_dev", role="founder")


def verify_jwt(token: str) -> Principal:
    """Verify a bearer token and return the caller principal.

    TODO(Sprint 1): validate the Supabase JWT signature and required claims.
    """
    raise NotImplementedError("JWT verification is implemented in Phase 1 Sprint 1")
