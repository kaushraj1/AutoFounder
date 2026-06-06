"""Database layer: async engine/session and the Unified Data Access Layer (UDAL)."""

from app.db.cache import CacheClient
from app.db.context import (
    TenantContextMissing,
    get_tenant_context,
    require_tenant_context,
    reset_tenant_context,
    set_tenant_context,
)
from app.db.graph import GraphClient
from app.db.object_store import ObjectClient
from app.db.redis_pool import close_redis, get_redis, init_redis
from app.db.relational import RelationalClient
from app.db.session import SessionLocal, engine, get_session
from app.db.udal import UDAL, CrossTenantViolation
from app.db.vector import VectorClient

__all__ = [
    # UDAL façade
    "UDAL",
    "CrossTenantViolation",
    # Clients (returned by UDAL accessors)
    "RelationalClient",
    "VectorClient",
    "GraphClient",
    "ObjectClient",
    "CacheClient",
    # Session
    "engine",
    "SessionLocal",
    "get_session",
    # Redis pool
    "init_redis",
    "close_redis",
    "get_redis",
    # Tenant context
    "set_tenant_context",
    "get_tenant_context",
    "require_tenant_context",
    "reset_tenant_context",
    "TenantContextMissing",
]
