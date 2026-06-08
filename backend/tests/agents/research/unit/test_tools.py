"""T2/T3 — tool wrappers: parse results + no-key raises ToolError."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.agents.base import ToolError
from app.agents.research.tools.crunchbase import search as crunchbase_search
from app.agents.research.tools.g2 import search as g2_search
from app.agents.research.tools.serpapi import search as serpapi_search
from app.agents.research.tools.similarweb import search as similarweb_search
from app.agents.research.tools.tavily import search as tavily_search

# ---------------------------------------------------------------------------
# Tavily
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_tavily_parses_results() -> None:
    respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"title": "Report", "url": "https://a.com", "content": "15% CAGR"}]},
        )
    )
    async with httpx.AsyncClient() as client:
        citations = await tavily_search(client, "AI scheduling market", api_key="key123")
    assert len(citations) == 1
    assert citations[0].source == "tavily"
    assert citations[0].snippet == "15% CAGR"


@pytest.mark.asyncio
async def test_tavily_no_key_raises_tool_error() -> None:
    async with httpx.AsyncClient() as client:
        with pytest.raises(ToolError):
            await tavily_search(client, "query", api_key="")


# ---------------------------------------------------------------------------
# SerpAPI
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_serpapi_parses_organic_results() -> None:
    respx.get("https://serpapi.com/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "organic_results": [
                    {"title": "SERP Result", "link": "https://b.com", "snippet": "some info"}
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        citations = await serpapi_search(client, "query", api_key="key456")
    assert citations[0].source == "serpapi"
    assert citations[0].url == "https://b.com"


@pytest.mark.asyncio
async def test_serpapi_no_key_raises_tool_error() -> None:
    async with httpx.AsyncClient() as client:
        with pytest.raises(ToolError):
            await serpapi_search(client, "query", api_key="")


# ---------------------------------------------------------------------------
# Crunchbase
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_crunchbase_parses_response() -> None:
    respx.get(url__regex=r"https://api\.crunchbase\.com/.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "properties": {
                    "short_description": "AI company",
                    "funding_total": 25.0,
                    "num_employees_enum": "employee_range_51_200",
                    "website_url": "https://aicompany.com",
                }
            },
        )
    )
    async with httpx.AsyncClient() as client:
        citations = await crunchbase_search(client, "AI Company", api_key="cbkey")
    assert citations[0].source == "crunchbase"
    assert "Funding" in citations[0].snippet


@pytest.mark.asyncio
async def test_crunchbase_no_key_raises_tool_error() -> None:
    async with httpx.AsyncClient() as client:
        with pytest.raises(ToolError):
            await crunchbase_search(client, "Company X", api_key="")


# ---------------------------------------------------------------------------
# G2
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_g2_parses_products() -> None:
    respx.get("https://data.g2.com/api/v1/products").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "attributes": {
                            "name": "Product A",
                            "star_rating": 4.5,
                            "reviews_count": 200,
                            "url": "https://g2.com/products/a",
                        }
                    }
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        citations = await g2_search(client, "Product A", api_key="g2key")
    assert citations[0].source == "g2"
    assert "4.5" in citations[0].snippet


@pytest.mark.asyncio
async def test_g2_no_key_raises_tool_error() -> None:
    async with httpx.AsyncClient() as client:
        with pytest.raises(ToolError):
            await g2_search(client, "product", api_key="")


# ---------------------------------------------------------------------------
# SimilarWeb
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_similarweb_parses_visits() -> None:
    respx.get(url__regex=r"https://api\.similarweb\.com/.*").mock(
        return_value=httpx.Response(200, json={"visits": [{"visits": 500000, "bounce_rate": 0.42}]})
    )
    async with httpx.AsyncClient() as client:
        citations = await similarweb_search(client, "notion.so", api_key="swkey")
    assert citations[0].source == "similarweb"
    assert "500000" in citations[0].snippet


@pytest.mark.asyncio
async def test_similarweb_no_key_raises_tool_error() -> None:
    async with httpx.AsyncClient() as client:
        with pytest.raises(ToolError):
            await similarweb_search(client, "notion.so", api_key="")
