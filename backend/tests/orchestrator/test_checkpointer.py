"""Integration tests for DualCheckpointer (AF-033).

Docker/Postgres is not available in CI for these tests, so the
``orchestrator.checkpoints`` table is emulated by an in-memory dict-backed
async session that honours the exact SQL DualCheckpointer issues
(INSERT / SELECT-latest / SELECT-by-id / list). This exercises the *real*
checkpointer code — ``aput`` / ``aget_tuple`` / ``alist`` / ``_row_to_tuple``,
JSON serialization, and the Redis mirror — end-to-end through a real
LangGraph graph (run → pause at gate → resume).

The raw SQL strings themselves are still only validated against a live
Postgres in a Docker-enabled environment; this proves the integration contract.
"""

from __future__ import annotations

import itertools
from typing import Any

import fakeredis.aioredis
import pytest

langgraph = pytest.importorskip("langgraph", reason="agents dep group not installed")

from app.orchestrator.checkpointer import DualCheckpointer  # noqa: E402
from app.orchestrator.graph import build_run_graph  # noqa: E402
from app.orchestrator.state import make_initial_state  # noqa: E402

# ---------------------------------------------------------------------------
# In-memory fake of the orchestrator.checkpoints table
# ---------------------------------------------------------------------------


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> _FakeResult:
        return self

    def first(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeSession:
    """Emulates AsyncSession against a shared dict store keyed by checkpoint id."""

    def __init__(
        self, store: dict[tuple[str, str, str], dict[str, Any]], seq: itertools.count
    ) -> None:
        self._store = store
        self._seq = seq

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> _FakeResult:
        sql = str(stmt)
        params = params or {}

        if sql.strip().upper().startswith("INSERT"):
            key = (params["run_id"], params["ns"], params["cid"])
            self._store[key] = {
                "run_id": params["run_id"],
                "checkpoint_ns": params["ns"],
                "checkpoint_id": params["cid"],
                "parent_checkpoint_id": params["parent_id"],
                "checkpoint": params["cp"],  # JSON string, as JSONB→str would return
                "metadata": params["meta"],
                "_order": next(self._seq),
            }
            return _FakeResult([])

        # SELECT — filter by run_id + ns
        rows = [
            r
            for r in self._store.values()
            if r["run_id"] == params.get("run_id") and r["checkpoint_ns"] == params.get("ns")
        ]
        if "cid" in params:
            rows = [r for r in rows if r["checkpoint_id"] == params["cid"]]
        if "before_cid" in params:
            rows = [r for r in rows if r["checkpoint_id"] < params["before_cid"]]
        rows.sort(key=lambda r: r["_order"], reverse=True)  # ORDER BY created_at DESC
        if params.get("limit") is not None:
            rows = rows[: params["limit"]]
        return _FakeResult([dict(r) for r in rows])

    async def commit(self) -> None:
        return None


def _factory(store: dict[tuple[str, str, str], dict[str, Any]], seq: itertools.count) -> Any:
    def make() -> _FakeSession:
        return _FakeSession(store, seq)

    return make


def _config(run_id: str) -> dict:
    return {"configurable": {"thread_id": run_id, "checkpoint_ns": ""}}


@pytest.fixture
def store() -> dict[tuple[str, str, str], dict[str, Any]]:
    return {}


@pytest.fixture
def redis() -> Any:
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def checkpointer(store: dict, redis: Any) -> DualCheckpointer:
    return DualCheckpointer(session_factory=_factory(store, itertools.count()), redis=redis)


# ---------------------------------------------------------------------------
# Low-level round-trip
# ---------------------------------------------------------------------------


async def test_aput_then_aget_roundtrip(checkpointer: DualCheckpointer) -> None:
    run_id = "11111111-1111-1111-1111-111111111111"
    config = _config(run_id)
    checkpoint = {"v": 1, "id": "cp-1", "channel_values": {"status": "running"}}

    saved_config = await checkpointer.aput(config, checkpoint, {"source": "loop"}, {})
    assert saved_config["configurable"]["checkpoint_id"] == "cp-1"

    tup = await checkpointer.aget_tuple(config)
    assert tup is not None
    assert tup.checkpoint["channel_values"]["status"] == "running"
    assert tup.config["configurable"]["thread_id"] == run_id


async def test_aput_mirrors_to_redis(checkpointer: DualCheckpointer, redis: Any) -> None:
    run_id = "22222222-2222-2222-2222-222222222222"
    await checkpointer.aput(_config(run_id), {"v": 1, "id": "cp-1", "channel_values": {}}, {}, {})
    raw = await redis.get(f"orch:checkpoint:{run_id}")
    assert raw is not None  # hot cache populated


async def test_aget_falls_back_to_postgres_without_redis(store: dict) -> None:
    """A checkpointer with redis=None must read straight from the DB store."""
    seq = itertools.count()
    run_id = "33333333-3333-3333-3333-333333333333"
    writer = DualCheckpointer(session_factory=_factory(store, seq), redis=None)
    await writer.aput(_config(run_id), {"v": 1, "id": "cp-1", "channel_values": {"x": 1}}, {}, {})

    reader = DualCheckpointer(session_factory=_factory(store, seq), redis=None)
    tup = await reader.aget_tuple(_config(run_id))
    assert tup is not None
    assert tup.checkpoint["channel_values"]["x"] == 1


async def test_alist_returns_all_checkpoints(checkpointer: DualCheckpointer) -> None:
    run_id = "44444444-4444-4444-4444-444444444444"
    for i in range(3):
        await checkpointer.aput(
            _config(run_id), {"v": 1, "id": f"cp-{i}", "channel_values": {}}, {}, {}
        )
    listed = [t async for t in checkpointer.alist(_config(run_id))]
    assert len(listed) == 3


# ---------------------------------------------------------------------------
# End-to-end: a real graph driven entirely by DualCheckpointer
# ---------------------------------------------------------------------------


async def test_graph_runs_and_resumes_on_dual_checkpointer(
    checkpointer: DualCheckpointer,
) -> None:
    graph = build_run_graph(checkpointer)
    run_id = "55555555-5555-5555-5555-555555555555"
    config = _config(run_id)

    # Initial invoke → must persist checkpoints and pause at validation_gate
    await graph.ainvoke(make_initial_state(run_id, "org-1", "ws-1", "DevTool idea"), config)
    snapshot = await graph.aget_state(config)
    assert snapshot.values["current_pillar"] == 1
    assert "validation_gate" in snapshot.next

    # Resume approved → state restored from checkpointer, advances to pillar 2
    await graph.aupdate_state(config, {"gate_decision": "approved"})
    await graph.ainvoke(None, config)
    snapshot = await graph.aget_state(config)
    assert snapshot.values["current_pillar"] == 2
    assert "architecture_gate" in snapshot.next


async def test_durability_resume_with_fresh_graph_instance(store: dict, redis: Any) -> None:
    """Simulate a process restart: a brand-new graph object backed by the same
    store + redis must resume the paused run from persisted checkpoints."""
    seq = itertools.count()
    run_id = "66666666-6666-6666-6666-666666666666"

    cp1 = DualCheckpointer(session_factory=_factory(store, seq), redis=redis)
    graph1 = build_run_graph(cp1)
    await graph1.ainvoke(
        make_initial_state(run_id, "org-1", "ws-1", "Resume idea"), _config(run_id)
    )

    # New checkpointer + graph (no shared in-memory graph state), same backing store
    cp2 = DualCheckpointer(session_factory=_factory(store, seq), redis=redis)
    graph2 = build_run_graph(cp2)
    restored = await graph2.aget_state(_config(run_id))
    assert restored.values["current_pillar"] == 1
    assert "validation_gate" in restored.next

    await graph2.aupdate_state(_config(run_id), {"gate_decision": "approved"})
    await graph2.ainvoke(None, _config(run_id))
    final = await graph2.aget_state(_config(run_id))
    assert final.values["current_pillar"] == 2
