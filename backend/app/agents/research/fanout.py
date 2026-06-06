"""Parallel tool fan-out for Research Agent.

Fan-out strategy:
- All sources run concurrently with per-tool asyncio.timeout.
- Tavily <-> SerpAPI cross-fallback: if Tavily fails, retry with SerpAPI (and vice versa).
- Crunchbase / G2 / SimilarWeb failures degrade gracefully → SourceResult(ok=False).
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from app.agents.research.schema import Citation, SourceResult

logger = logging.getLogger("app.agents.research.fanout")

_SEARCH_SOURCES = {"tavily", "serpapi"}
_FALLBACK = {"tavily": "serpapi", "serpapi": "tavily"}


async def _call_one(
    call_tool: Callable[[str, dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]],
    source: str,
    query: str,
    limit: int,
    timeout: float,
) -> SourceResult:
    try:
        async with asyncio.timeout(timeout):
            raw = await call_tool(source, {"query": query, "limit": limit})
        citations = [Citation(**c) for c in raw.get("citations", [])]
        return SourceResult(source=source, ok=True, items=citations)
    except TimeoutError:
        logger.warning("Tool '%s' timed out after %.1fs", source, timeout)
        return SourceResult(source=source, ok=False, error=f"timed out after {timeout}s")
    except Exception as exc:
        logger.warning("Tool '%s' failed: %s", source, exc)
        return SourceResult(source=source, ok=False, error=str(exc))


async def fan_out(
    call_tool: Callable[[str, dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]],
    query: str,
    sources: list[str],
    *,
    limit: int = 5,
    per_tool_timeout: float = 20.0,
) -> list[SourceResult]:
    """Run all sources in parallel, apply cross-fallback for search sources."""
    tasks = {
        s: asyncio.create_task(_call_one(call_tool, s, query, limit, per_tool_timeout))
        for s in sources
    }
    results_raw = dict(zip(tasks.keys(), await asyncio.gather(*tasks.values()), strict=True))

    results: list[SourceResult] = []
    attempted_fallback: set[str] = set()

    for source, result in results_raw.items():
        if result.ok:
            results.append(result)
            continue

        fallback = _FALLBACK.get(source)
        if fallback and fallback not in sources and fallback not in attempted_fallback:
            # primary not in sources list either — try fallback
            logger.info("'%s' failed, trying fallback '%s'", source, fallback)
            attempted_fallback.add(fallback)
            fb_result = await _call_one(call_tool, fallback, query, limit, per_tool_timeout)
            results.append(fb_result if fb_result.ok else result)
        elif fallback and fallback in results_raw and not results_raw[fallback].ok:
            # both primary + fallback failed → cross-fallback: retry opposite
            logger.info("Both '%s' and '%s' failed — cross-retry '%s'", source, fallback, fallback)
            if fallback not in attempted_fallback:
                attempted_fallback.add(fallback)
                fb_result = await _call_one(call_tool, fallback, query, limit, per_tool_timeout)
                if fb_result.ok:
                    results.append(fb_result)
                    continue
            results.append(result)
        else:
            results.append(result)

    return results
