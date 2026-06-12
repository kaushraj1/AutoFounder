"""Unit tests for the UDAL and tenant context subsystem.

No real database is required — the session is mocked with AsyncMock.
Tests verify:
  - ContextVar is set on UDAL construction.
  - Cross-tenant guard raises CrossTenantViolation when org_ids diverge.
  - Same-tenant guard passes silently.
  - graph() always raises NotImplementedError regardless of tenant state.
  - relational() sets search_path correctly.
  - ObjectClient scopes all paths to the tenant prefix.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.core.security import Principal
from app.db.context import get_tenant_context, reset_tenant_context, set_tenant_context
from app.db.graph import GraphClient
from app.db.object_store import ObjectClient
from app.db.udal import UDAL, CrossTenantViolation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_udal(org_id: str = "org_alpha") -> tuple[UDAL, AsyncMock]:
    principal = Principal(organization_id=org_id, role="founder")
    session = AsyncMock()
    session.execute = AsyncMock()
    udal = UDAL(principal, session)
    return udal, session


# ---------------------------------------------------------------------------
# ContextVar tests
# ---------------------------------------------------------------------------


def test_context_set_on_udal_init() -> None:
    udal, _ = _make_udal("org_test_ctx")
    assert get_tenant_context() == "org_test_ctx"


def test_context_isolated_per_token() -> None:
    token = set_tenant_context("org_first")
    assert get_tenant_context() == "org_first"
    reset_tenant_context(token)


# ---------------------------------------------------------------------------
# Cross-tenant guard tests
# ---------------------------------------------------------------------------


def test_same_tenant_guard_passes() -> None:
    udal, _ = _make_udal("org_same")
    # Should not raise
    udal._guard()


def test_cross_tenant_guard_raises() -> None:
    udal, _ = _make_udal("org_a")
    # Manually overwrite context to simulate a concurrent UDAL in same Task
    token = set_tenant_context("org_b")
    try:
        with pytest.raises(CrossTenantViolation, match="SEV-1"):
            udal._guard()
    finally:
        reset_tenant_context(token)
        # Restore original so other tests are unaffected
        set_tenant_context("org_a")


def test_guard_passes_when_context_is_none() -> None:
    """Guard is a no-op if nothing else has set the ContextVar."""
    udal, _ = _make_udal("org_c")
    # Forcefully clear the context (reset to None)
    from app.db.context import _org_id_var

    token = _org_id_var.set(None)
    try:
        udal._guard()  # should not raise
    finally:
        _org_id_var.reset(token)


# ---------------------------------------------------------------------------
# graph() always raises NotImplementedError
# ---------------------------------------------------------------------------


def test_graph_raises_not_implemented() -> None:
    udal, _ = _make_udal("org_graph")
    gc: GraphClient = udal.graph()
    with pytest.raises(NotImplementedError, match="Open Decisions"):
        gc.query("MATCH (n) RETURN n")


def test_graph_upsert_node_raises() -> None:
    udal, _ = _make_udal("org_graph2")
    gc = udal.graph()
    with pytest.raises(NotImplementedError):
        gc.upsert_node("Person", {"name": "Alice"})


# ---------------------------------------------------------------------------
# relational() sets search_path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_relational_sets_search_path() -> None:
    udal, session = _make_udal("org_rel")
    async with udal.relational() as db:
        assert db.session is session
        # Verify SET LOCAL was called with the correct org schema
        calls = session.execute.call_args_list
        assert len(calls) == 2
        sql_text_1 = str(calls[0][0][0])
        sql_text_2 = str(calls[1][0][0])
        assert "org_org_rel" in sql_text_1
        assert "SET LOCAL search_path" in sql_text_1
        assert "SET LOCAL app.organization_id" in sql_text_2


@pytest.mark.asyncio
async def test_relational_guard_runs_before_session_use() -> None:
    udal, _ = _make_udal("org_guard_rel")
    token = set_tenant_context("org_other")
    try:
        with pytest.raises(CrossTenantViolation):
            udal.relational()
    finally:
        reset_tenant_context(token)
        set_tenant_context("org_guard_rel")


# ---------------------------------------------------------------------------
# vector() returns VectorClient with correct org_id
# ---------------------------------------------------------------------------


def test_vector_returns_correct_org() -> None:
    udal, _ = _make_udal("org_vec")
    vc = udal.vector()
    assert vc._org_id == "org_vec"


# ---------------------------------------------------------------------------
# ObjectClient path scoping
# ---------------------------------------------------------------------------


def test_object_client_prefixes_path() -> None:
    client = ObjectClient(org_id="abc123")
    assert client._full_path("artifacts/file.json") == "org_abc123/artifacts/file.json"


def test_object_client_strips_leading_slash() -> None:
    client = ObjectClient(org_id="abc123")
    assert client._full_path("/deep/path/file.pdf") == "org_abc123/deep/path/file.pdf"


def test_object_client_empty_path() -> None:
    client = ObjectClient(org_id="abc123")
    assert client._full_path("") == "org_abc123/"


# ---------------------------------------------------------------------------
# UDAL.organization_id property
# ---------------------------------------------------------------------------


def test_udal_organization_id_property() -> None:
    udal, _ = _make_udal("org_prop")
    assert udal.organization_id == "org_prop"
