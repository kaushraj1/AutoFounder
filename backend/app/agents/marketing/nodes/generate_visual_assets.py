"""Node 8 — generate_visual_assets (AF-044).

Generates DALL-E 3 prompts + (optionally) calls DALL-E 3 API for 4 brand visuals.
Runs in parallel with Nodes 3–7.
DALL-E generation is non-fatal — degrades to prompt-only if API unavailable.

Reads:  brand_config, brand_voice, target_audience_summary
Writes: visual_asset_bundle
"""

from __future__ import annotations

import asyncio
import logging

from app.agents.marketing.llm import call_llm
from app.agents.marketing.prompt_loader import render
from app.agents.marketing.state import MarketerState
from app.agents.marketing.tools.dalle_generate import dalle_generate

logger = logging.getLogger(__name__)

# Inter-image delay to stay under DALL-E 5 img/min limit
_DALL_E_DELAY = 12.0


async def generate_visual_assets(state: MarketerState) -> MarketerState:
    """LangGraph node: generate DALL-E 3 prompts + optionally call the API."""
    logger.info("[marketing] generate_visual_assets — start")

    list(state.get("errors", []))

    # ---- Step 1: Generate DALL-E prompts via Gemini ----
    prompt = render(
        "generate_visual_assets",
        brand_config=state.get("brand_config", {}),
        brand_voice=state.get("brand_voice", ""),
        target_audience_summary=state.get("target_audience_summary", ""),
    )

    try:
        prompts_result, tokens = await call_llm(prompt, temperature=0.5)
    except Exception as exc:
        err = f"generate_visual_assets: prompt generation failed: {exc}"
        logger.error("[marketing] %s", err)
        return {
            "visual_asset_bundle": {"total_generated": 0, "status": "failed"},
            "errors": [err],
        }

    # ---- Step 2: Call DALL-E 3 for each asset (sequential, rate-limited) ----
    asset_types = ["logo", "og_image", "social_card", "email_banner"]
    sizes = {
        "logo": "1024x1024",
        "og_image": "1792x1024",
        "social_card": "1024x1024",
        "email_banner": "1792x1024",
    }

    generated_bundle: dict = {}
    total_generated = 0

    for i, asset_type in enumerate(asset_types):
        asset_prompts = prompts_result.get(asset_type) or {}
        dall_e_prompt = asset_prompts.get("dall_e_prompt", "")

        if not dall_e_prompt:
            logger.warning("[marketing] generate_visual_assets: no prompt for %s", asset_type)
            generated_bundle[asset_type] = {
                "asset_type": asset_type,
                "dall_e_prompt": "",
                "generated_url": None,
                "status": "skipped",
            }
            continue

        # Rate limit: wait between images
        if i > 0:
            await asyncio.sleep(_DALL_E_DELAY)

        result = await dalle_generate(
            dall_e_prompt,
            size=sizes.get(asset_type, "1024x1024"),
            asset_type=asset_type,
        )
        generated_bundle[asset_type] = result

        if result.get("generated_url"):
            total_generated += 1

    generated_bundle["total_generated"] = total_generated

    logger.info(
        "[marketing] generate_visual_assets — done: generated=%d/4 tokens=%d",
        total_generated,
        tokens,
    )

    return {
        "visual_asset_bundle": generated_bundle,
        "images_generated": total_generated,
        "llm_tokens_used": tokens,
    }
