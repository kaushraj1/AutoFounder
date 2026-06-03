"""Shared FastAPI dependencies."""

from app.core.security import DEV_PRINCIPAL, Principal


def get_principal() -> Principal:
    """Resolve the calling principal.

    Phase 1 returns a fixed development principal so endpoints work without an identity
    provider. Sprint 1 reads the Authorization header, calls ``verify_jwt``, and returns
    the real tenant principal — which then scopes every UDAL query.
    """
    return DEV_PRINCIPAL
