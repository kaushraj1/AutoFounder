"""Local ToolRegistryProtocol adapter for Research Agent.

Dispatches tool_name -> tools/*.py HTTP functions.
Swap this for the real AF-047 Tool Registry later — protocol unchanged.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.agents.base import ToolRegistryProtocol
from app.agents.research.schema import Citation
from app.agents.research.tools import (
    crunchbase_search,
    g2_search,
    serpapi_search,
    similarweb_search,
    tavily_search,
)
from app.core.config import get_settings

logger = logging.getLogger("app.agents.research.registry")

_MOCK_CITATIONS: dict[str, list[dict[str, Any]]] = {
    "tavily": [{"source": "tavily", "url": "https://example.com/mock-tavily",
                "title": "Mock Tavily Result", "snippet": "Mock market data from Tavily."}],
    "serpapi": [{"source": "serpapi", "url": "https://example.com/mock-serp",
                 "title": "Mock SerpAPI Result", "snippet": "Mock market data from SerpAPI."}],
    "crunchbase": [{"source": "crunchbase", "url": "https://crunchbase.com/mock",
                    "title": "Mock Company", "snippet": "Funding: $5M | Employees: 11-50"}],
    "g2": [{"source": "g2", "url": "https://g2.com/mock",
            "title": "Mock Product", "snippet": "G2 rating: 4.2/5 from 128 reviews"}],
    "similarweb": [{"source": "similarweb", "url": "https://similarweb.com/mock",
                    "title": "Traffic data: example.com",
                    "snippet": "Monthly visits: 50000 | Bounce: 0.45"}],
}


class ResearchToolRegistry(ToolRegistryProtocol):
    """Routes research tool calls to individual tool wrappers.

    Falls back to mock data when API keys are missing so CI stays green.
    Logs a loud warning so missing keys are visible.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        query: str = args.get("query") or args.get("domain") or args.get("company_name") or ""
        limit: int = int(args.get("limit", 5))

        try:
            citations = await self._dispatch(tool_name, query, limit)
            return {"citations": [c.model_dump() for c in citations]}
        except Exception as exc:
            logger.error("Tool %s failed: %s", tool_name, exc)
            raise

    async def _dispatch(self, tool_name: str, query: str, limit: int) -> list[Citation]:
        s = self.settings

        async with httpx.AsyncClient() as client:
            if tool_name == "tavily":
                if not s.tavily_api_key:
                    return self._mock(tool_name, "TAVILY_API_KEY")
                return await tavily_search(client, query, api_key=s.tavily_api_key, limit=limit)

            if tool_name == "serpapi":
                if not s.serpapi_key:
                    return self._mock(tool_name, "SERPAPI_KEY")
                return await serpapi_search(client, query, api_key=s.serpapi_key, limit=limit)

            if tool_name == "crunchbase":
                if not s.crunchbase_api_key:
                    return self._mock(tool_name, "CRUNCHBASE_API_KEY")
                return await crunchbase_search(
                    client, query, api_key=s.crunchbase_api_key, limit=limit
                )

            if tool_name == "g2":
                if not s.g2_api_key:
                    return self._mock(tool_name, "G2_API_KEY")
                return await g2_search(client, query, api_key=s.g2_api_key, limit=limit)

            if tool_name == "similarweb":
                if not s.similarweb_api_key:
                    return self._mock(tool_name, "SIMILARWEB_API_KEY")
                return await similarweb_search(
                    client, query, api_key=s.similarweb_api_key, limit=limit
                )

        raise NotImplementedError(f"Unknown research tool: {tool_name}")

    def _mock(self, tool_name: str, env_var: str) -> list[Citation]:
        logger.warning(
            "%s not configured — returning MOCK data for tool '%s'. "
            "Research findings will be ungrounded.",
            env_var,
            tool_name,
        )
        return [Citation(**c) for c in _MOCK_CITATIONS.get(tool_name, [])]
