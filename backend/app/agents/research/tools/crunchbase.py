"""Crunchbase company lookup tool wrapper."""
from __future__ import annotations

import httpx

from app.agents.base import ToolError
from app.agents.research.schema import Citation

_ENDPOINT = "https://api.crunchbase.com/api/v4/entities/organizations"
_FIELD_IDS = "short_description,funding_total,num_employees_enum,founded_on,website_url"


async def search(
    client: httpx.AsyncClient,
    query: str,
    *,
    api_key: str,
    limit: int = 3,
) -> list[Citation]:
    if not api_key:
        raise ToolError("CRUNCHBASE_API_KEY not configured", agent_id="research")

    slug = query.lower().replace(" ", "-")
    resp = await client.get(
        f"{_ENDPOINT}/{slug}",
        params={"user_key": api_key, "field_ids": _FIELD_IDS},
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()
    props = data.get("properties", {})

    snippet_parts = [props.get("short_description", "")]
    if props.get("funding_total"):
        snippet_parts.append(f"Funding: ${props['funding_total']}M")
    if props.get("num_employees_enum"):
        snippet_parts.append(f"Employees: {props['num_employees_enum']}")

    return [
        Citation(
            source="crunchbase",
            url=props.get("website_url") or f"https://www.crunchbase.com/organization/{slug}",
            title=query,
            snippet=" | ".join(p for p in snippet_parts if p),
        )
    ]
