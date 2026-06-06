"""G2 product reviews tool wrapper."""
from __future__ import annotations

import httpx

from app.agents.base import ToolError
from app.agents.research.schema import Citation

_ENDPOINT = "https://data.g2.com/api/v1/products"


async def search(
    client: httpx.AsyncClient,
    query: str,
    *,
    api_key: str,
    limit: int = 3,
) -> list[Citation]:
    if not api_key:
        raise ToolError("G2_API_KEY not configured", agent_id="research")

    resp = await client.get(
        _ENDPOINT,
        headers={"Authorization": f"Token token={api_key}"},
        params={"filter[name]": query, "page[size]": limit},
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()

    citations: list[Citation] = []
    for product in data.get("data", []):
        attrs = product.get("attributes", {})
        rating = attrs.get("star_rating")
        review_count = attrs.get("reviews_count", 0)
        snippet = f"G2 rating: {rating}/5 from {review_count} reviews" if rating else ""
        citations.append(
            Citation(
                source="g2",
                url=attrs.get("url"),
                title=attrs.get("name", query),
                snippet=snippet,
            )
        )
    return citations
