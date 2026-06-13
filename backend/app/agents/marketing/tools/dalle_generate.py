"""DALL-E 3 image generation tool for the Marketing Agent (AF-044).

Used by: generate_visual_assets
Rate limit: 5 images/min
Fallback: Return prompt only (generated_url=None); non-fatal degradation
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_RATE_LIMIT_DELAY = 12.0  # seconds between images to stay under 5/min


async def dalle_generate(
    prompt: str,
    *,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid",
    asset_type: str = "unknown",
) -> dict[str, Any]:
    """Generate an image with DALL-E 3.

    Args:
        prompt: The image generation prompt (50–150 words recommended).
        size: "1024x1024" | "1792x1024" | "1024x1792"
        quality: "standard" | "hd"
        style: "vivid" | "natural"
        asset_type: Human label for logging (e.g. "logo", "og_image")

    Returns:
        Dict with "generated_url" (str | None), "status", "asset_type", "dall_e_prompt".
        generated_url is None if generation fails (non-fatal).
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning(
            "[marketing/dalle] OPENAI_API_KEY not set — returning prompt only for %s",
            asset_type,
        )
        return _prompt_only(prompt, asset_type, reason="no_api_key")

    try:
        from openai import AsyncOpenAI
    except ImportError:
        logger.warning(
            "[marketing/dalle] openai package not installed — returning prompt only for %s",
            asset_type,
        )
        return _prompt_only(prompt, asset_type, reason="openai_not_installed")

    client = AsyncOpenAI(api_key=api_key)

    for attempt in range(1, 4):
        try:
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=1,
            )
            url = response.data[0].url
            logger.info(
                "[marketing/dalle] generated %s (attempt %d): %s...",
                asset_type,
                attempt,
                (url or "")[:60],
            )
            return {
                "asset_type": asset_type,
                "dall_e_prompt": prompt,
                "generated_url": url,
                "status": "generated",
            }
        except Exception as exc:
            logger.warning(
                "[marketing/dalle] %s generation failed (attempt %d): %s",
                asset_type,
                attempt,
                exc,
            )
            if attempt < 3:
                await asyncio.sleep(60.0 if "rate_limit" in str(exc).lower() else 5.0)

    return _prompt_only(prompt, asset_type, reason="all_retries_failed")


def _prompt_only(prompt: str, asset_type: str, reason: str = "") -> dict[str, Any]:
    """Return prompt-only result (graceful degradation)."""
    logger.info("[marketing/dalle] %s degraded to prompt-only (reason=%s)", asset_type, reason)
    return {
        "asset_type": asset_type,
        "dall_e_prompt": prompt,
        "generated_url": None,
        "status": "failed",
        "reason": reason,
    }
