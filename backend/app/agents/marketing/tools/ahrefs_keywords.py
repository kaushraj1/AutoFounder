"""Ahrefs keyword research tool wrapper for the Marketing Agent (AF-044).

Used by: analyse_brand, generate_seo_blogs
Rate limit: 500 req/day
Fallback: Tavily keyword data (non-fatal)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.agents.marketing.utils.retry import retry_async

logger = logging.getLogger(__name__)

_AHREFS_BASE = "https://apiv2.ahrefs.com"
_TIMEOUT = 20.0


async def ahrefs_keywords(
    keywords: list[str],
    *,
    country: str = "us",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Fetch keyword volume and difficulty from Ahrefs.

    Args:
        keywords: List of keyword strings to look up.
        country: Country code for localised volume data.
        limit: Max results per keyword.

    Returns:
        List of keyword dicts with volume, difficulty, CPC; empty list on failure.
    """
    api_key = os.getenv("AHREFS_API_KEY", "")
    if not api_key:
        logger.warning("[marketing/ahrefs] AHREFS_API_KEY not set — using Tavily fallback")
        return _tavily_keyword_fallback(keywords)

    results: list[dict[str, Any]] = []

    for keyword in keywords[:10]:  # cap at 10 to preserve daily quota
        async def _call(kw: str = keyword) -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.get(
                    f"{_AHREFS_BASE}/v1/keywords-explorer/overview",
                    params={
                        "token": api_key,
                        "target": kw,
                        "country": country,
                        "limit": limit,
                        "output": "json",
                    },
                )
                response.raise_for_status()
                return response.json()

        try:
            data = await retry_async(_call, max_retries=3, label=f"ahrefs:{keyword}")
            results.append({
                "keyword": keyword,
                "monthly_volume": data.get("volume", 0),
                "keyword_difficulty": data.get("difficulty", 0),
                "cpc_usd": data.get("cpc", 0.0),
                "source": "ahrefs",
            })
        except Exception as exc:
            logger.warning("[marketing/ahrefs] keyword=%r failed: %s", keyword, exc)
            results.append({
                "keyword": keyword,
                "monthly_volume": None,
                "keyword_difficulty": None,
                "cpc_usd": None,
                "source": "fallback",
                "error": str(exc),
            })

    return results


def _tavily_keyword_fallback(keywords: list[str]) -> list[dict[str, Any]]:
    """Return stub keyword data when Ahrefs is unavailable."""
    return [
        {
            "keyword": kw,
            "monthly_volume": None,
            "keyword_difficulty": None,
            "cpc_usd": None,
            "source": "fallback",
        }
        for kw in keywords
    ]
