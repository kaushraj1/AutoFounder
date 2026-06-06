"""SimilarWeb traffic data tool wrapper."""

from __future__ import annotations

import httpx

from app.agents.base import ToolError
from app.agents.research.schema import Citation

_ENDPOINT = "https://api.similarweb.com/v1/website"


async def search(
    client: httpx.AsyncClient,
    query: str,
    *,
    api_key: str,
    limit: int = 3,
) -> list[Citation]:
    if not api_key:
        raise ToolError("SIMILARWEB_API_KEY not configured", agent_id="research")

    # query is expected to be a bare domain (e.g. "notion.so")
    domain = query.lower().replace("https://", "").replace("http://", "").split("/")[0]

    resp = await client.get(
        f"{_ENDPOINT}/{domain}/total-traffic-and-engagement/visits",
        params={"api_key": api_key, "country": "world", "granularity": "monthly", "limit": 1},
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()

    visits = data.get("visits", [])
    snippet = ""
    if visits:
        latest = visits[-1]
        v = latest.get("visits", "N/A")
        b = latest.get("bounce_rate", "N/A")
        snippet = f"Monthly visits: {v} | Bounce: {b}"

    return [
        Citation(
            source="similarweb",
            url=f"https://www.similarweb.com/website/{domain}/",
            title=f"Traffic data: {domain}",
            snippet=snippet,
        )
    ]
