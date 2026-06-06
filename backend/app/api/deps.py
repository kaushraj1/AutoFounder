"""Shared FastAPI dependencies."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import DEV_PRINCIPAL, Principal, verify_jwt, verify_mtls
from app.db.context import reset_tenant_context, set_tenant_context
from app.db.redis_pool import get_redis as _get_redis
from app.db.session import get_session
from app.db.udal import UDAL
from app.guardrails.opa import check_opa_policy
from app.schemas.common import Meta

security = HTTPBearer(auto_error=False)


def get_redis() -> aioredis.Redis:
    """Return the app-level Redis client (FastAPI dependency)."""
    return _get_redis()


async def get_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> AsyncIterator[Principal]:
    """Resolve the calling principal and manage request-scoped tenant ContextVar.

    Validates mTLS (if enabled), verifies Supabase JWT, and evaluates OPA authorization.
    """
    settings = get_settings()

    # 1. mTLS Verification
    if not verify_mtls(request):
        raise ForbiddenError("mTLS Verification Failed")

    # 2. Token extraction & validation
    principal = None
    if credentials is not None:
        try:
            principal = verify_jwt(credentials.credentials)
        except ValueError as e:
            raise UnauthorizedError(str(e)) from e
    else:
        if not settings.is_production:
            principal = DEV_PRINCIPAL
        else:
            raise UnauthorizedError("Missing or invalid Authorization header")

    # 3. OPA authorization check
    allow, reason = await check_opa_policy(
        organization_id=principal.organization_id,
        role=principal.role,
        scopes=principal.scopes,
        action=request.method,
        resource=request.url.path,
    )
    if not allow:
        raise ForbiddenError(reason or "OPA authorization check denied access")

    # 4. Request-scoped tenant ContextVar ingress
    token = set_tenant_context(principal.organization_id)
    try:
        yield principal
    finally:
        reset_tenant_context(token)


async def get_udal(
    principal: Annotated[Principal, Depends(get_principal)],
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> UDAL:
    """Construct a tenant-scoped UDAL for the current request.

    Injects the authenticated principal, a request-scoped async session,
    and the app-level Redis client.  All data access goes through UDAL.
    """
    return UDAL(principal, session, redis=redis)


def get_meta(request: Request) -> Meta:
    """Resolve response metadata including request_id and current timestamp."""
    return Meta(
        request_id=getattr(request.state, "request_id", "unknown"),
        timestamp=datetime.now(UTC),
    )
