"""OrchestratorEngine — manages run lifecycle over the StateGraph (AF-033).

Lazily builds the StateGraph on first use so importing this module never
requires langgraph to be installed (it lives in the optional `agents` dep group).

Two persistence layers are kept in sync:
  - ``orchestrator.checkpoints`` (LangGraph durable state, via DualCheckpointer)
  - ``org_{org_id}.runs`` (the lifecycle row queried by ``GET /v1/runs/{id}``)

Usage (production):
    engine = OrchestratorEngine(session_factory=SessionLocal, redis=get_redis())
    run_id = await engine.create_run(org_id, ws_id, idea_text, created_by=user)
    await engine.resume(run_id, "approved")

Usage (tests):
    engine = OrchestratorEngine()          # uses MemorySaver, no DB writes
    engine._graph = build_run_graph(MemorySaver())
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# Gate nodes the graph pauses before (mirror of graph._GATE_NODES).
_GATE_NODES = frozenset({"validation_gate", "architecture_gate", "infra_spend_gate", "launch_gate"})
# Terminal DB statuses for the runs row.
_TERMINAL = frozenset({"completed", "failed", "cancelled"})


class OrchestratorEngine:
    """Drives a founder idea through the 7-pillar pipeline."""

    def __init__(
        self,
        session_factory: Any = None,
        redis: Any = None,
    ) -> None:
        self._session_factory = session_factory
        self._redis = redis
        self._graph: Any = None  # CompiledStateGraph, built lazily

    # ------------------------------------------------------------------
    # Internal — graph
    # ------------------------------------------------------------------

    def _get_graph(self) -> Any:
        if self._graph is None:
            from app.orchestrator.graph import build_run_graph

            checkpointer = None
            if self._session_factory is not None:
                from app.orchestrator.checkpointer import DualCheckpointer

                checkpointer = DualCheckpointer(
                    session_factory=self._session_factory,
                    redis=self._redis,
                )
            # build_run_graph falls back to MemorySaver when checkpointer is None
            self._graph = build_run_graph(checkpointer)
        return self._graph

    @staticmethod
    def _config(run_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": run_id, "checkpoint_ns": ""}}

    # ------------------------------------------------------------------
    # Internal — runs table persistence (tenant-scoped)
    # ------------------------------------------------------------------

    async def _persist_run_row(
        self,
        run_id: str,
        organization_id: str,
        workspace_id: str,
        idea_text: str,
        idea_meta: dict[str, Any],
        created_by: str,
    ) -> None:
        """INSERT the lifecycle row into ``org_{org_id}.runs``.

        No-op when no session factory is configured (pure-graph tests).
        """
        if self._session_factory is None:
            return
        import json

        from sqlalchemy import text

        async with self._session_factory() as session:
            await session.execute(
                text(f'SET LOCAL search_path TO "org_{organization_id}", platform, public;')
            )
            await session.execute(text(f"SET LOCAL app.organization_id = '{organization_id}';"))
            await session.execute(
                text("""
                    INSERT INTO runs
                        (id, workspace_id, organization_id, status,
                         idea_text, idea_meta, created_by)
                    VALUES
                        (CAST(:id AS UUID), CAST(:ws AS UUID), CAST(:org AS UUID),
                         'running', :idea, CAST(:meta AS JSONB), :by)
                """),
                {
                    "id": run_id,
                    "ws": workspace_id,
                    "org": organization_id,
                    "idea": idea_text,
                    "meta": json.dumps(idea_meta),
                    "by": created_by,
                },
            )
            await session.commit()

    async def _update_run_status(self, run_id: str, organization_id: str, status: str) -> None:
        """Sync the runs row status; stamps started_at / completed_at."""
        if self._session_factory is None:
            return
        from sqlalchemy import text

        is_terminal = status in _TERMINAL
        async with self._session_factory() as session:
            await session.execute(
                text(f'SET LOCAL search_path TO "org_{organization_id}", platform, public;')
            )
            await session.execute(text(f"SET LOCAL app.organization_id = '{organization_id}';"))
            await session.execute(
                text("""
                    UPDATE runs
                       SET status = :status,
                           started_at = COALESCE(started_at, now()),
                           completed_at = CASE WHEN :is_terminal
                                               THEN now() ELSE completed_at END
                     WHERE id = CAST(:id AS UUID)
                """),
                {"status": status, "is_terminal": is_terminal, "id": run_id},
            )
            await session.commit()

    @staticmethod
    def _derive_status(snapshot: Any) -> str:
        """Map a LangGraph snapshot to a runs.status value.

        - paused at a HITL gate            → ``paused``
        - graph ended                      → in-state status (``completed``/``failed``)
        - mid-pipeline (more work queued)  → ``running``
        """
        next_nodes = set(snapshot.next or ())
        if next_nodes & _GATE_NODES:
            return "paused"
        if not next_nodes:
            state_status = (snapshot.values or {}).get("status")
            return state_status if state_status in _TERMINAL else "completed"
        return "running"

    async def _sync_status_from_graph(self, run_id: str, organization_id: str) -> None:
        snapshot = await self._get_graph().aget_state(self._config(run_id))
        await self._update_run_status(run_id, organization_id, self._derive_status(snapshot))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_run(
        self,
        organization_id: str,
        workspace_id: str,
        idea_text: str,
        idea_meta: dict[str, Any] | None = None,
        created_by: str = "system",
    ) -> str:
        """Start a new run.

        Persists the runs row, then invokes the graph, which executes
        ``validate_input`` and ``run_pillar_1`` and pauses at ``validation_gate``
        (the first HITL interrupt). The runs row status is synced afterwards.

        Returns the new ``run_id`` (UUID string).
        """
        from app.orchestrator.state import make_initial_state

        run_id = str(uuid4())
        idea_meta = idea_meta or {}

        await self._persist_run_row(
            run_id, organization_id, workspace_id, idea_text, idea_meta, created_by
        )

        initial = make_initial_state(
            run_id=run_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            idea_text=idea_text,
            idea_meta=idea_meta,
        )
        config = self._config(run_id)
        await self._get_graph().ainvoke(initial, config)

        # Create gate if paused (AF-034)
        if self._session_factory is not None:
            async with self._session_factory() as session:
                from sqlalchemy import text

                await session.execute(
                    text(f'SET LOCAL search_path TO "org_{organization_id}", platform, public;')
                )
                await session.execute(text(f"SET LOCAL app.organization_id = '{organization_id}';"))
                snapshot = await self._get_graph().aget_state(config)
                from app.orchestrator.hitl.gate_manager import check_and_create_gate

                await check_and_create_gate(
                    run_id=run_id,
                    org_id=organization_id,
                    snapshot=snapshot,
                    db_session=session,
                    graph=self._get_graph(),
                    config=config,
                )

        await self._sync_status_from_graph(run_id, organization_id)
        logger.info("run=%s created", run_id)
        return run_id

    async def resume(
        self,
        run_id: str,
        gate_decision: str,
        pivot_text: str | None = None,
    ) -> None:
        """Resume a run paused at a HITL gate.

        Args:
            run_id: The run to resume.
            gate_decision: ``"approved" | "rejected" | "timed_out"``.
            pivot_text: Optional new ``idea_text`` for a pivot re-run.
                        Only meaningful when ``gate_decision == "rejected"``.
        """
        graph = self._get_graph()
        config = self._config(run_id)

        update: dict[str, Any] = {
            "gate_decision": gate_decision,
            "active_gate_id": None,
        }
        if pivot_text is not None:
            update["idea_text"] = pivot_text

        await graph.aupdate_state(config, update)
        await graph.ainvoke(None, config)

        # organization_id is authoritative in the graph state.
        snapshot = await graph.aget_state(config)
        org_id = (snapshot.values or {}).get("organization_id")

        # Create next gate if paused after resume (AF-034)
        if org_id and self._session_factory is not None:
            async with self._session_factory() as session:
                from sqlalchemy import text

                await session.execute(
                    text(f'SET LOCAL search_path TO "org_{org_id}", platform, public;')
                )
                await session.execute(text(f"SET LOCAL app.organization_id = '{org_id}';"))
                from app.orchestrator.hitl.gate_manager import check_and_create_gate

                await check_and_create_gate(
                    run_id=run_id,
                    org_id=org_id,
                    snapshot=snapshot,
                    db_session=session,
                    graph=graph,
                    config=config,
                )

        if org_id:
            await self._update_run_status(run_id, org_id, self._derive_status(snapshot))
        logger.info("run=%s resumed gate_decision=%s", run_id, gate_decision)

    async def get_run_state(self, run_id: str) -> dict[str, Any] | None:
        """Return the current RunState values for a run.

        Returns None if no checkpoint exists (run not found).
        """
        graph = self._get_graph()
        snapshot = await graph.aget_state(self._config(run_id))
        if snapshot is None or not snapshot.values:
            return None
        return dict(snapshot.values)
