"""Buffer scheduling tool for the Marketing Agent (AF-044).

Used by: schedule_posts (LinkedIn posts)
Rate limit: 10 req/s
Fallback: Mark post as "draft" (non-fatal); cross-fallback to Typefully if unavailable
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from app.agents.marketing.utils.retry import retry_async

logger = logging.getLogger(__name__)

_BUFFER_BASE = "https://api.bufferapp.com/1"
_TIMEOUT = 15.0


async def buffer_schedule(
    content: str,
    *,
    profile_id: str = "",
    scheduled_at: str = "",  # ISO 8601 datetime or "" for "next available slot"
    channel: str = "linkedin",
) -> dict[str, Any]:
    """Schedule a post via Buffer API.

    Args:
        content: Post text content.
        profile_id: Buffer profile ID. Reads from BUFFER_PROFILE_ID env if empty.
        scheduled_at: ISO 8601 datetime string (optional; uses next slot if empty).
        channel: Channel label for logging.

    Returns:
        Dict with "post_id", "status", "channel"; status="draft" on failure (non-fatal).
    """
    access_token = os.getenv("BUFFER_ACCESS_TOKEN", "")
    if not access_token:
        logger.warning("[marketing/buffer] BUFFER_ACCESS_TOKEN not set — marking as draft")
        return _draft_result(channel, reason="no_access_token")

    pid = profile_id or os.getenv("BUFFER_PROFILE_ID", "")
    if not pid:
        logger.warning("[marketing/buffer] No BUFFER_PROFILE_ID — marking as draft")
        return _draft_result(channel, reason="no_profile_id")

    payload: dict[str, Any] = {
        "text": content,
        "profile_ids[]": pid,
        "access_token": access_token,
    }
    if scheduled_at:
        payload["scheduled_at"] = scheduled_at

    async def _call() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BUFFER_BASE}/updates/create.json",
                data=payload,
            )
            response.raise_for_status()
            return response.json()

    try:
        result = await retry_async(_call, max_retries=3, label="buffer_schedule")
        post_id = result.get("updates", [{}])[0].get("id", "unknown")
        logger.info("[marketing/buffer] scheduled %s post_id=%s", channel, post_id)
        return {"post_id": post_id, "status": "scheduled", "channel": channel}
    except Exception as exc:
        logger.warning("[marketing/buffer] scheduling failed: %s — marking as draft", exc)
        return _draft_result(channel, reason=str(exc))


def _draft_result(channel: str, reason: str = "") -> dict[str, Any]:
    return {"post_id": None, "status": "draft", "channel": channel, "reason": reason}
