"""Tavily search tool wrapper."""

from __future__ import annotations

import httpx

from app.agents.base import ToolError
from app.agents.research.schema import Citation

_ENDPOINT = "https://api.tavily.com/search"


async def search(
    client: httpx.AsyncClient,
    query: str,
    *,
    api_key: str,
    limit: int = 5,
) -> list[Citation]:
    if not api_key:
        raise ToolError("TAVILY_API_KEY not configured", agent_id="research")

    resp = await client.post(
        _ENDPOINT,
        json={
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": limit,
        },
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()

    return [
        Citation(
            source="tavily",
            url=r.get("url"),
            title=r.get("title"),
            snippet=r.get("content", ""),
        )
        for r in data.get("results", [])
    ]
