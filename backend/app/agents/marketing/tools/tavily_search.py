"""Tavily search tool wrapper for the Marketing Agent (AF-044).

Used by: analyse_brand (competitor/positioning research)
Rate limit: 60 req/min
Fallback: LLM training knowledge (non-fatal)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.agents.marketing.utils.retry import retry_async

logger = logging.getLogger(__name__)

_TAVILY_BASE = "https://api.tavily.com"
_TIMEOUT = 20.0


async def tavily_search(
    query: str,
    *,
    max_results: int = 5,
    search_depth: str = "basic",  # "basic" | "advanced"
) -> dict[str, Any]:
    """Search the web via Tavily API.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.
        search_depth: "basic" (faster) or "advanced" (deeper).

    Returns:
        Dict with "results" list; empty dict on failure (non-fatal).
    """
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        logger.warning("[marketing/tavily] TAVILY_API_KEY not set — skipping search")
        return {"results": [], "fallback": True}

    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": True,
    }

    async def _call() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{_TAVILY_BASE}/search", json=payload)
            response.raise_for_status()
            return response.json()

    try:
        result = await retry_async(_call, max_retries=3, label="tavily_search")
        logger.info(
            "[marketing/tavily] query=%r results=%d",
            query[:60],
            len(result.get("results", [])),
        )
        return result
    except Exception as exc:
        logger.warning("[marketing/tavily] search failed (using LLM fallback): %s", exc)
        return {"results": [], "fallback": True, "error": str(exc)}
