"""Tenant context propagation via contextvars.

Each async request/task carries exactly one organization_id in a ContextVar.
The UDAL sets it on construction; the cross-tenant guard reads it on every
accessor call.  This means any code that runs inside the same asyncio Task
(agents, tools, background coroutines) automatically inherits the tenant scope
without passing the id through every call frame.
"""

from contextvars import ContextVar, Token

_org_id_var: ContextVar[str | None] = ContextVar("organization_id", default=None)


def set_tenant_context(org_id: str) -> Token[str | None]:
    """Set the current tenant.  Returns a Token for optional reset."""
    return _org_id_var.set(org_id)


def reset_tenant_context(token: Token[str | None]) -> None:
    """Reset to the previous value (use in finally blocks when needed)."""
    _org_id_var.reset(token)


def get_tenant_context() -> str | None:
    """Return the current org_id or None if not set."""
    return _org_id_var.get()


def require_tenant_context() -> str:
    """Return the current org_id or raise if not set."""
    org_id = _org_id_var.get()
    if org_id is None:
        raise TenantContextMissing(
            "No tenant context in ContextVar — UDAL must be constructed before calling this."
        )
    return org_id


class TenantContextMissing(RuntimeError):
    """Raised when tenant context is required but not set."""
