"""Unit tests for CacheClient (AF-032).

Uses fakeredis — no real Redis required.
Covers all five cache types: session, checkpoint, prompt_cache, embedding, cost.
"""

from __future__ import annotations

import fakeredis.aioredis
import pytest

from app.db.cache import CacheClient

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
async def cache() -> CacheClient:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return CacheClient(org_id="org_test", redis=redis)


@pytest.fixture
async def other_cache() -> CacheClient:
    """Same Redis server, different org — verifies key isolation."""
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return CacheClient(org_id="org_other", redis=redis)


# ---------------------------------------------------------------------------
# Session cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_session_set_get(cache: CacheClient) -> None:
    await cache.set_session("sess_1", {"user": "alice", "plan": "pro"})
    result = await cache.get_session("sess_1")
    assert result == {"user": "alice", "plan": "pro"}


@pytest.mark.asyncio
async def test_session_missing_returns_none(cache: CacheClient) -> None:
    assert await cache.get_session("nonexistent") is None


@pytest.mark.asyncio
async def test_session_delete(cache: CacheClient) -> None:
    await cache.set_session("sess_del", {"x": 1})
    await cache.delete_session("sess_del")
    assert await cache.get_session("sess_del") is None


# ---------------------------------------------------------------------------
# LangGraph checkpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_checkpoint_set_get(cache: CacheClient) -> None:
    state = {"step": "strategy", "result": {"score": 0.9}}
    await cache.set_checkpoint("run_abc", "strategy_node", state)
    result = await cache.get_checkpoint("run_abc", "strategy_node")
    assert result == state


@pytest.mark.asyncio
async def test_checkpoint_missing_returns_none(cache: CacheClient) -> None:
    assert await cache.get_checkpoint("run_xyz", "missing_node") is None


@pytest.mark.asyncio
async def test_checkpoint_delete_run(cache: CacheClient) -> None:
    await cache.set_checkpoint("run_del", "node_a", {"a": 1})
    await cache.set_checkpoint("run_del", "node_b", {"b": 2})
    await cache.delete_run_checkpoints("run_del")
    assert await cache.get_checkpoint("run_del", "node_a") is None
    assert await cache.get_checkpoint("run_del", "node_b") is None


@pytest.mark.asyncio
async def test_checkpoint_delete_other_run_unaffected(cache: CacheClient) -> None:
    await cache.set_checkpoint("run_keep", "node_x", {"keep": True})
    await cache.set_checkpoint("run_gone", "node_y", {"gone": True})
    await cache.delete_run_checkpoints("run_gone")
    assert await cache.get_checkpoint("run_keep", "node_x") == {"keep": True}


# ---------------------------------------------------------------------------
# Semantic prompt cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prompt_cache_hit(cache: CacheClient) -> None:
    prompt = "What is the TAM for edtech in India?"
    response = "The TAM is approximately $10B."
    await cache.set_prompt_cache(prompt, response)
    assert await cache.get_prompt_cache(prompt) == response


@pytest.mark.asyncio
async def test_prompt_cache_miss(cache: CacheClient) -> None:
    assert await cache.get_prompt_cache("unseen prompt") is None


@pytest.mark.asyncio
async def test_prompt_cache_different_prompts(cache: CacheClient) -> None:
    await cache.set_prompt_cache("prompt A", "response A")
    await cache.set_prompt_cache("prompt B", "response B")
    assert await cache.get_prompt_cache("prompt A") == "response A"
    assert await cache.get_prompt_cache("prompt B") == "response B"


# ---------------------------------------------------------------------------
# Embedding cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embedding_set_get(cache: CacheClient) -> None:
    text = "AutoFounder AI platform"
    embedding = [0.1, 0.2, 0.3, 0.4]
    await cache.set_embedding(text, embedding)
    result = await cache.get_embedding(text)
    assert result == embedding


@pytest.mark.asyncio
async def test_embedding_missing_returns_none(cache: CacheClient) -> None:
    assert await cache.get_embedding("never stored") is None


# ---------------------------------------------------------------------------
# Per-tenant cost accumulator
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cost_accumulate_and_get(cache: CacheClient) -> None:
    total = await cache.accumulate_cost(500, "2026-06-05")
    assert total == 500
    total = await cache.accumulate_cost(300, "2026-06-05")
    assert total == 800
    assert await cache.get_cost("2026-06-05") == 800


@pytest.mark.asyncio
async def test_cost_zero_for_new_period(cache: CacheClient) -> None:
    assert await cache.get_cost("2099-01-01") == 0


@pytest.mark.asyncio
async def test_cost_periods_isolated(cache: CacheClient) -> None:
    await cache.accumulate_cost(100, "2026-06-01")
    await cache.accumulate_cost(200, "2026-06-02")
    assert await cache.get_cost("2026-06-01") == 100
    assert await cache.get_cost("2026-06-02") == 200


# ---------------------------------------------------------------------------
# Tenant key isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_keys_isolated_across_orgs() -> None:
    shared_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    cache_a = CacheClient(org_id="org_a", redis=shared_redis)
    cache_b = CacheClient(org_id="org_b", redis=shared_redis)

    await cache_a.set_session("sid", {"tenant": "a"})
    # org_b must not see org_a's session
    assert await cache_b.get_session("sid") is None
    assert await cache_a.get_session("sid") == {"tenant": "a"}
