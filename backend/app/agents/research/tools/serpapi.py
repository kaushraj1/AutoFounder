"""SerpAPI search tool wrapper (Tavily fallback)."""
from __future__ import annotations

import httpx

from app.agents.base import ToolError
from app.agents.research.schema import Citation

_ENDPOINT = "https://serpapi.com/search"


async def search(
    client: httpx.AsyncClient,
    query: str,
    *,
    api_key: str,
    limit: int = 5,
) -> list[Citation]:
    if not api_key:
        raise ToolError("SERPAPI_KEY not configured", agent_id="research")

    resp = await client.get(
        _ENDPOINT,
        params={
            "api_key": api_key,
            "q": query,
            "engine": "google",
            "num": limit,
        },
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()

    results = data.get("organic_results") or data.get("results", [])
    return [
        Citation(
            source="serpapi",
            url=r.get("link"),
            title=r.get("title"),
            snippet=r.get("snippet", ""),
        )
        for r in results[:limit]
    ]
