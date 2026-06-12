"""Typefully scheduling tool for the Marketing Agent (AF-044).

Used by: schedule_posts (X/Twitter threads)
Rate limit: 10 req/s
Fallback: Mark thread as "draft"; cross-fallback to Buffer if unavailable
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.agents.marketing.utils.retry import retry_async

logger = logging.getLogger(__name__)

_TYPEFULLY_BASE = "https://api.typefully.com/v1"
_TIMEOUT = 15.0


async def typefully_schedule(
    tweets: list[str],
    *,
    scheduled_at: str = "",  # ISO 8601 or "" for next slot
    auto_retweet_enabled: bool = False,
    auto_plug_enabled: bool = False,
) -> dict[str, Any]:
    """Schedule an X thread via Typefully API.

    Args:
        tweets: List of tweet strings (each ≤280 chars).
        scheduled_at: ISO 8601 datetime or "" to schedule at next best time.
        auto_retweet_enabled: Typefully auto-retweet feature.
        auto_plug_enabled: Typefully auto-plug feature.

    Returns:
        Dict with "thread_id", "status", "channel"; status="draft" on failure (non-fatal).
    """
    api_key = os.getenv("TYPEFULLY_API_KEY", "")
    if not api_key:
        logger.warning("[marketing/typefully] TYPEFULLY_API_KEY not set — marking as draft")
        return _draft_result(reason="no_api_key")

    # Typefully expects tweets joined by a special separator
    thread_content = "\n\n---\n\n".join(tweets)

    payload: dict[str, Any] = {
        "content": thread_content,
        "auto-retweet-enabled": auto_retweet_enabled,
        "auto-plug-enabled": auto_plug_enabled,
    }
    if scheduled_at:
        payload["schedule-date"] = scheduled_at
    else:
        payload["next-free-slot"] = True

    headers = {"X-API-KEY": f"Bearer {api_key}", "Content-Type": "application/json"}

    async def _call() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_TYPEFULLY_BASE}/drafts/",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    try:
        result = await retry_async(_call, max_retries=3, label="typefully_schedule")
        thread_id = result.get("id", "unknown")
        logger.info("[marketing/typefully] scheduled X thread thread_id=%s", thread_id)
        return {"thread_id": thread_id, "status": "scheduled", "channel": "x"}
    except Exception as exc:
        logger.warning("[marketing/typefully] scheduling failed: %s — marking as draft", exc)
        return _draft_result(reason=str(exc))


def _draft_result(reason: str = "") -> dict[str, Any]:
    return {"thread_id": None, "status": "draft", "channel": "x", "reason": reason}
