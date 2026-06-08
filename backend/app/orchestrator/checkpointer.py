"""Dual checkpointer: PostgreSQL (durable) + Redis hot cache (AF-033).

PostgreSQL (orchestrator.checkpoints) is the authoritative store.
Redis (orch:checkpoint:{run_id}) is a 24-hour hot cache for fast checkpoint
reads on resume — avoids a Postgres round-trip.

Imported lazily by the orchestrator engine (only when a session factory is
configured), so the optional ``agents`` dependency group is never required at
top-level application import time.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Sequence
from typing import Any

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)

logger = logging.getLogger(__name__)

_CHECKPOINT_TTL = 86_400  # 24 h


class DualCheckpointer(BaseCheckpointSaver):
    """PostgreSQL + Redis LangGraph checkpointer.

    Args:
        session_factory: ``async_sessionmaker`` instance from ``app.db.session``.
        redis: Optional ``aioredis.Redis`` client; if None Redis writes are skipped.
    """

    def __init__(self, session_factory: Any, redis: Any = None) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._redis = redis

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _redis_key(self, thread_id: str) -> str:
        return f"orch:checkpoint:{thread_id}"

    def _row_to_tuple(self, row: dict[str, Any]) -> CheckpointTuple:
        thread_id = str(row["run_id"])
        ns = row.get("checkpoint_ns", "")
        cid = row["checkpoint_id"]
        parent_id = row.get("parent_checkpoint_id")

        cp = row["checkpoint"]
        if isinstance(cp, str):
            cp = json.loads(cp)

        meta = row.get("metadata", {})
        if isinstance(meta, str):
            meta = json.loads(meta)

        this_config: Any = {
            "configurable": {"thread_id": thread_id, "checkpoint_ns": ns, "checkpoint_id": cid}
        }
        parent_config: Any = (
            {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": ns,
                    "checkpoint_id": parent_id,
                }
            }
            if parent_id
            else None
        )
        return CheckpointTuple(
            config=this_config,
            checkpoint=cp,
            metadata=meta,
            parent_config=parent_config,
            pending_writes=[],
        )

    # ------------------------------------------------------------------
    # Async interface (used by the async graph)
    # ------------------------------------------------------------------

    async def aget_tuple(self, config: Any) -> CheckpointTuple | None:
        thread_id: str = config["configurable"]["thread_id"]
        ns: str = config["configurable"].get("checkpoint_ns", "")
        cid: str | None = config["configurable"].get("checkpoint_id")

        # Hot path: Redis (only for "get latest" without a specific checkpoint_id)
        if cid is None and self._redis is not None:
            try:
                raw = await self._redis.get(self._redis_key(thread_id))
                if raw:
                    return self._row_to_tuple(json.loads(raw))
            except Exception:
                logger.debug("Redis checkpoint miss for run %s", thread_id)

        # Cold path: Postgres
        from sqlalchemy import text

        if cid:
            sql = text("""
                SELECT run_id::text AS run_id, checkpoint_ns, checkpoint_id,
                       parent_checkpoint_id, checkpoint, metadata
                FROM orchestrator.checkpoints
                WHERE run_id = CAST(:run_id AS UUID)
                  AND checkpoint_ns = :ns
                  AND checkpoint_id = :cid
                LIMIT 1
            """)
            params: dict[str, Any] = {"run_id": thread_id, "ns": ns, "cid": cid}
        else:
            sql = text("""
                SELECT run_id::text AS run_id, checkpoint_ns, checkpoint_id,
                       parent_checkpoint_id, checkpoint, metadata
                FROM orchestrator.checkpoints
                WHERE run_id = CAST(:run_id AS UUID)
                  AND checkpoint_ns = :ns
                ORDER BY created_at DESC
                LIMIT 1
            """)
            params = {"run_id": thread_id, "ns": ns}

        async with self._session_factory() as session:
            result = await session.execute(sql, params)
            row = result.mappings().first()

        return self._row_to_tuple(dict(row)) if row else None

    async def alist(
        self,
        config: Any | None,
        *,
        filter: dict[str, Any] | None = None,
        before: Any | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        from sqlalchemy import text

        parts = [
            "SELECT run_id::text AS run_id, checkpoint_ns, checkpoint_id,",
            "       parent_checkpoint_id, checkpoint, metadata",
            "FROM orchestrator.checkpoints WHERE 1=1",
        ]
        params: dict[str, Any] = {}

        if config:
            thread_id: str = config["configurable"]["thread_id"]
            ns: str = config["configurable"].get("checkpoint_ns", "")
            parts.append("AND run_id = CAST(:run_id AS UUID)")
            parts.append("AND checkpoint_ns = :ns")
            params.update({"run_id": thread_id, "ns": ns})

        if before:
            before_cid = before["configurable"].get("checkpoint_id")
            if before_cid:
                parts.append("AND checkpoint_id < :before_cid")
                params["before_cid"] = before_cid

        parts.append("ORDER BY created_at DESC")

        if limit is not None:
            parts.append("LIMIT :limit")
            params["limit"] = limit

        async with self._session_factory() as session:
            result = await session.execute(text(" ".join(parts)), params)
            rows = result.mappings().all()

        for row in rows:
            yield self._row_to_tuple(dict(row))

    async def aput(
        self,
        config: Any,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> Any:
        from sqlalchemy import text

        thread_id: str = config["configurable"]["thread_id"]
        ns: str = config["configurable"].get("checkpoint_ns", "")
        parent_id: str | None = config["configurable"].get("checkpoint_id")
        cid: str = checkpoint["id"]

        cp_json = json.dumps(checkpoint, default=str)
        meta_json = json.dumps(dict(metadata), default=str)

        async with self._session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO orchestrator.checkpoints
                        (run_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
                         type, checkpoint, metadata)
                    VALUES
                        (CAST(:run_id AS UUID), :ns, :cid, :parent_id,
                         'json', CAST(:cp AS JSONB), CAST(:meta AS JSONB))
                    ON CONFLICT (run_id, checkpoint_ns, checkpoint_id) DO UPDATE
                        SET checkpoint = EXCLUDED.checkpoint,
                            metadata   = EXCLUDED.metadata
                """),
                {
                    "run_id": thread_id,
                    "ns": ns,
                    "cid": cid,
                    "parent_id": parent_id,
                    "cp": cp_json,
                    "meta": meta_json,
                },
            )
            await session.commit()

        # Mirror to Redis hot cache
        if self._redis is not None:
            try:
                hot = {
                    "run_id": thread_id,
                    "checkpoint_ns": ns,
                    "checkpoint_id": cid,
                    "parent_checkpoint_id": parent_id,
                    "checkpoint": checkpoint,
                    "metadata": dict(metadata),
                }
                await self._redis.set(
                    self._redis_key(thread_id),
                    json.dumps(hot, default=str),
                    ex=_CHECKPOINT_TTL,
                )
            except Exception:
                logger.warning("Redis checkpoint mirror failed for run %s", thread_id)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": ns,
                "checkpoint_id": cid,
            }
        }

    async def aput_writes(
        self,
        config: Any,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        # Intermediate (mid-superstep) writes are not persisted separately.
        # Stub nodes are idempotent, so a crash safely re-runs the superstep.
        # Revisit when non-idempotent agent nodes land (AF-036+).
        return None

    # ------------------------------------------------------------------
    # Sync stubs (required by ABC; unused in the async FastAPI app)
    # ------------------------------------------------------------------

    def get_tuple(self, config: Any) -> CheckpointTuple | None:
        raise NotImplementedError("DualCheckpointer is async-only; use aget_tuple")

    def list(self, config: Any | None, **kwargs: Any) -> Any:
        raise NotImplementedError("DualCheckpointer is async-only; use alist")

    def put(
        self,
        config: Any,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> Any:
        raise NotImplementedError("DualCheckpointer is async-only; use aput")

    def put_writes(
        self,
        config: Any,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        raise NotImplementedError("DualCheckpointer is async-only; use aput_writes")
