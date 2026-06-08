"""Tests for OrchestratorEngine ↔ runs-table persistence (AF-033).

Verifies that ``create_run`` writes a ``runs`` row and that the lifecycle
status is synced to ``paused`` at a HITL gate and ``completed`` at the end.

Postgres is emulated by an in-memory fake session that handles BOTH the
``orchestrator.checkpoints`` writes (driven by DualCheckpointer) and the
``runs`` INSERT/UPDATE issued by the engine. SET LOCAL statements are no-ops.
"""

from __future__ import annotations

import itertools
from typing import Any

import fakeredis.aioredis
import pytest

langgraph = pytest.importorskip("langgraph", reason="agents dep group not installed")

from app.orchestrator.engine import OrchestratorEngine  # noqa: E402


class _Result:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> _Result:
        return self

    def first(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _Store:
    """Shared backing state across all sessions from one factory."""

    def __init__(self) -> None:
        self.checkpoints: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.seq = itertools.count()


class _Session:
    def __init__(self, store: _Store) -> None:
        self._s = store

    async def __aenter__(self) -> _Session:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> _Result:
        sql = " ".join(str(stmt).split())
        p = params or {}
        upper = sql.upper()

        if upper.startswith("SET LOCAL"):
            return _Result([])

        if "INSERT INTO ORCHESTRATOR.CHECKPOINTS" in upper:
            key = (p["run_id"], p["ns"], p["cid"])
            self._s.checkpoints[key] = {
                "run_id": p["run_id"],
                "checkpoint_ns": p["ns"],
                "checkpoint_id": p["cid"],
                "parent_checkpoint_id": p["parent_id"],
                "checkpoint": p["cp"],
                "metadata": p["meta"],
                "_order": next(self._s.seq),
            }
            return _Result([])

        if "FROM ORCHESTRATOR.CHECKPOINTS" in upper:
            rows = [
                r
                for r in self._s.checkpoints.values()
                if r["run_id"] == p.get("run_id") and r["checkpoint_ns"] == p.get("ns")
            ]
            if "cid" in p:
                rows = [r for r in rows if r["checkpoint_id"] == p["cid"]]
            rows.sort(key=lambda r: r["_order"], reverse=True)
            if p.get("limit") is not None:
                rows = rows[: p["limit"]]
            return _Result([dict(r) for r in rows])

        if upper.startswith("INSERT INTO RUNS"):
            self._s.runs[p["id"]] = {
                "id": p["id"],
                "workspace_id": p["ws"],
                "organization_id": p["org"],
                "status": "running",
                "idea_text": p["idea"],
                "created_by": p["by"],
            }
            return _Result([])

        if upper.startswith("UPDATE RUNS"):
            row = self._s.runs.get(p["id"])
            if row is not None:
                row["status"] = p["status"]
            return _Result([])

        return _Result([])

    async def commit(self) -> None:
        return None


def _factory(store: _Store) -> Any:
    def make() -> _Session:
        return _Session(store)

    return make


@pytest.fixture
def store() -> _Store:
    return _Store()


@pytest.fixture
def engine(store: _Store) -> OrchestratorEngine:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return OrchestratorEngine(session_factory=_factory(store), redis=redis)


async def test_create_run_inserts_runs_row(engine: OrchestratorEngine, store: _Store) -> None:
    run_id = await engine.create_run("org-1", "ws-1", "DevTool idea", created_by="alice")
    assert run_id in store.runs
    row = store.runs[run_id]
    assert row["idea_text"] == "DevTool idea"
    assert row["created_by"] == "alice"
    assert row["organization_id"] == "org-1"


async def test_create_run_status_paused_at_gate(engine: OrchestratorEngine, store: _Store) -> None:
    run_id = await engine.create_run("org-1", "ws-1", "idea")
    # Paused before validation_gate → runs row must reflect 'paused'
    assert store.runs[run_id]["status"] == "paused"


async def test_full_approve_marks_run_completed(engine: OrchestratorEngine, store: _Store) -> None:
    run_id = await engine.create_run("org-1", "ws-1", "Full pipeline idea")
    assert store.runs[run_id]["status"] == "paused"

    await engine.resume(run_id, "approved")  # validation
    assert store.runs[run_id]["status"] == "paused"  # now at architecture gate

    await engine.resume(run_id, "approved")  # architecture
    assert store.runs[run_id]["status"] == "paused"  # now at launch gate

    await engine.resume(run_id, "approved")  # launch → pillar 7 → done
    assert store.runs[run_id]["status"] == "completed"


async def test_checkpoints_persisted_to_store(engine: OrchestratorEngine, store: _Store) -> None:
    await engine.create_run("org-1", "ws-1", "Checkpoint idea")
    # The engine's DualCheckpointer must have written to the checkpoints store
    assert len(store.checkpoints) > 0
