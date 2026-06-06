"""Authentication / authorization helpers.

Phase 1 ships a permissive development principal so local flows work end-to-end without
a real identity provider. Sprint 1 replaces ``verify_jwt`` with Supabase JWT verification:
validate the signature with ``SUPABASE_JWT_SECRET`` and extract ``organization_id`` / ``role`` /
``scopes`` claims, which then flow into the Unified Data Access Layer for tenant scoping.
"""

from dataclasses import dataclass, field

import jwt
from fastapi import Request

from app.core.config import get_settings


@dataclass(frozen=True)
class Principal:
    """The authenticated caller. ``organization_id`` drives all tenant isolation."""

    organization_id: str
    role: str = "founder"
    scopes: list[str] = field(default_factory=list)


# Fixed principal used in development until real auth lands.
DEV_PRINCIPAL = Principal(
    organization_id="org_dev", role="founder", scopes=["runs:read", "runs:write", "gates:decide"]
)


def verify_jwt(token: str) -> Principal:
    """Verify a bearer token and return the caller principal.

    Validates the Supabase JWT signature and extracts organization_id, role, and scopes.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.supabase_jwt_secret, algorithms=["HS256"], options={"verify_aud": False}
        )
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid token: {e}") from e

    app_metadata = payload.get("app_metadata", {})
    user_metadata = payload.get("user_metadata", {})

    org_id = (
        payload.get("organization_id")
        or app_metadata.get("organization_id")
        or user_metadata.get("organization_id")
        or payload.get("sub")
    )

    if not org_id:
        raise ValueError("Missing organization_id claim")

    role = payload.get("role") or app_metadata.get("role") or "founder"

    scope_claim = payload.get("scope") or payload.get("scopes") or app_metadata.get("scopes") or []
    if isinstance(scope_claim, str):
        scopes = [s.strip() for s in scope_claim.split(" ") if s.strip()]
    elif isinstance(scope_claim, list):
        scopes = scope_claim
    else:
        scopes = []

    return Principal(organization_id=org_id, role=role, scopes=scopes)


def verify_mtls(request: Request) -> bool:
    """Verify that the request has a valid client certificate (mTLS).

    Checks proxy headers:
    - X-SSL-Client-Verify: SUCCESS (set by reverse proxy)
    - X-SSL-Client-DN: The DN of the client certificate (e.g. CN=orchestrator.internal)
    """
    settings = get_settings()
    if not settings.mtls_enabled:
        return True

    client_verify = request.headers.get("X-SSL-Client-Verify")
    client_dn = request.headers.get("X-SSL-Client-DN", "")

    if client_verify != "SUCCESS":
        return False

    allowed_dns = [dn.strip() for dn in settings.mtls_allowed_dns.split(",") if dn.strip()]
    if client_dn not in allowed_dns:
        return False

    return True
