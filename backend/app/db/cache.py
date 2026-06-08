"""Tenant-scoped Redis cache client (AF-032).

Key namespace: org:{org_id}:{type}:{...}

Five cache types:
  session      — org:{org_id}:session:{session_id}
  checkpoint   — org:{org_id}:checkpoint:{run_id}:{node}
  prompt_cache — org:{org_id}:llm:prompt_cache:{sha256(prompt)}
  embedding    — org:{org_id}:embedding:{sha256(text)}
  cost         — org:{org_id}:cost:{period}  (period = YYYY-MM-DD, value in USD cents)
"""

from __future__ import annotations

import hashlib
import json

import redis.asyncio as aioredis

_SESSION_TTL = 3_600  # 1 h
_CHECKPOINT_TTL = 86_400  # 24 h
_PROMPT_TTL = 3_600  # 1 h
_EMBEDDING_TTL = 86_400  # 24 h
_COST_TTL = 32 * 86_400  # 32 days — covers monthly billing window


class CacheClient:
    """Tenant-scoped Redis operations. Keys always prefixed org:{org_id}:."""

    def __init__(self, org_id: str, redis: aioredis.Redis) -> None:
        self._org_id = org_id
        self._r = redis

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _key(self, *parts: str) -> str:
        return f"org:{self._org_id}:{':'.join(parts)}"

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Session cache
    # ------------------------------------------------------------------

    async def set_session(self, session_id: str, data: dict, ttl: int = _SESSION_TTL) -> None:
        await self._r.set(self._key("session", session_id), json.dumps(data), ex=ttl)

    async def get_session(self, session_id: str) -> dict | None:
        raw = await self._r.get(self._key("session", session_id))
        return json.loads(raw) if raw else None

    async def delete_session(self, session_id: str) -> None:
        await self._r.delete(self._key("session", session_id))

    # ------------------------------------------------------------------
    # LangGraph plan checkpoints
    # ------------------------------------------------------------------

    async def set_checkpoint(
        self, run_id: str, node: str, state: dict, ttl: int = _CHECKPOINT_TTL
    ) -> None:
        await self._r.set(self._key("checkpoint", run_id, node), json.dumps(state), ex=ttl)

    async def get_checkpoint(self, run_id: str, node: str) -> dict | None:
        raw = await self._r.get(self._key("checkpoint", run_id, node))
        return json.loads(raw) if raw else None

    async def delete_run_checkpoints(self, run_id: str) -> None:
        """Delete all checkpoints for a run. Uses SCAN (non-blocking)."""
        pattern = self._key("checkpoint", run_id, "*")
        keys = [key async for key in self._r.scan_iter(match=pattern)]
        if keys:
            await self._r.delete(*keys)

    # ------------------------------------------------------------------
    # Semantic prompt cache
    # ------------------------------------------------------------------

    async def get_prompt_cache(self, prompt: str) -> str | None:
        raw = await self._r.get(self._key("llm", "prompt_cache", self._sha256(prompt)))
        return raw.decode() if isinstance(raw, bytes) else raw

    async def set_prompt_cache(self, prompt: str, response: str, ttl: int = _PROMPT_TTL) -> None:
        await self._r.set(self._key("llm", "prompt_cache", self._sha256(prompt)), response, ex=ttl)

    # ------------------------------------------------------------------
    # Embedding cache
    # ------------------------------------------------------------------

    async def get_embedding(self, text: str) -> list[float] | None:
        raw = await self._r.get(self._key("embedding", self._sha256(text)))
        return json.loads(raw) if raw else None

    async def set_embedding(
        self, text: str, embedding: list[float], ttl: int = _EMBEDDING_TTL
    ) -> None:
        await self._r.set(self._key("embedding", self._sha256(text)), json.dumps(embedding), ex=ttl)

    # ------------------------------------------------------------------
    # Per-tenant cost accumulator
    # ------------------------------------------------------------------

    async def accumulate_cost(self, amount_usd_cents: int, period: str) -> int:
        """Increment period cost by amount_usd_cents. Returns new total.

        period = YYYY-MM-DD. TTL auto-set on first write only (NX flag).
        """
        key = self._key("cost", period)
        total = int(await self._r.incrby(key, amount_usd_cents))
        await self._r.expire(key, _COST_TTL, nx=True)
        return total

    async def get_cost(self, period: str) -> int:
        """Return accumulated cost in USD cents for period, 0 if no data."""
        raw = await self._r.get(self._key("cost", period))
        return int(raw) if raw else 0
