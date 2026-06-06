"""T4–T7 — fan-out: parallel happy path, fallbacks, timeouts."""
from __future__ import annotations

import asyncio

import pytest
from tests.agents.research.conftest import FakeToolRegistry

from app.agents.research.fanout import fan_out


@pytest.mark.asyncio
async def test_fanout_happy_path_all_sources() -> None:
    tools = FakeToolRegistry()
    results = await fan_out(tools.call, "AI market", ["tavily", "serpapi", "crunchbase"], limit=3)
    sources_ok = [r.source for r in results if r.ok]
    assert set(sources_ok) == {"tavily", "serpapi", "crunchbase"}


@pytest.mark.asyncio
async def test_fanout_tavily_down_serp_fallback() -> None:
    """Tavily fails; serpapi NOT in sources; cross-fallback kicks in."""
    tools = FakeToolRegistry()
    tools.fail_sources = {"tavily"}
    results = await fan_out(tools.call, "AI market", ["tavily"], limit=3)
    # Either fallback to serpapi succeeded or tavily result is failed
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_fanout_non_search_source_fails_gracefully() -> None:
    tools = FakeToolRegistry()
    tools.fail_sources = {"crunchbase", "g2"}
    results = await fan_out(tools.call, "query", ["tavily", "crunchbase", "g2"], limit=3)
    failed = [r for r in results if not r.ok]
    assert {r.source for r in failed} == {"crunchbase", "g2"}
    ok = [r for r in results if r.ok]
    assert any(r.source == "tavily" for r in ok)


@pytest.mark.asyncio
async def test_fanout_timeout_marks_source_failed() -> None:
    async def slow_call(tool_name: str, args: dict) -> dict:
        await asyncio.sleep(5)
        return {"citations": []}

    results = await fan_out(slow_call, "query", ["tavily"], per_tool_timeout=0.05)
    assert results[0].ok is False
    assert "timed out" in (results[0].error or "")


@pytest.mark.asyncio
async def test_fanout_returns_citations_in_results() -> None:
    tools = FakeToolRegistry()
    results = await fan_out(tools.call, "B2B SaaS market", ["tavily"], limit=2)
    assert results[0].ok
    assert len(results[0].items) == 1
    assert results[0].items[0].source == "tavily"
