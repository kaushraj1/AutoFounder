"""Node 5 — generate_product_hunt_kit (AF-044).

Generates a complete Product Hunt launch kit with hard character-limit enforcement.
Runs in parallel with Nodes 3–4, 6–8.

Reads:  brand_config, feature_list, brand_voice, unique_value_proposition,
        competitor_gaps, target_audience_summary, effective_live_url
Writes: product_hunt_kit
"""

from __future__ import annotations

import logging

from app.agents.marketing.llm import call_llm
from app.agents.marketing.prompt_loader import render
from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)

# Product Hunt character limits
_TAGLINE_MAX = 60
_DESCRIPTION_MAX = 260
_FIRST_COMMENT_MAX = 1000
_MAKER_NOTE_MAX = 500


async def generate_product_hunt_kit(state: MarketerState) -> MarketerState:
    """LangGraph node: Product Hunt tagline, description, first comment, maker note."""
    logger.info("[marketing] generate_product_hunt_kit — start")

    errors: list[str] = list(state.get("errors", []))
    prompt = render(
        "generate_product_hunt_kit",
        brand_config=state.get("brand_config", {}),
        live_url=state.get("effective_live_url", "[PENDING_DEPLOY]"),
        brand_voice=state.get("brand_voice", ""),
        unique_value_proposition=state.get("unique_value_proposition", ""),
        target_audience_summary=state.get("target_audience_summary", ""),
        feature_list=state.get("feature_list", {}),
        competitor_gaps=state.get("competitor_gaps", []),
    )

    try:
        result, tokens = await call_llm(prompt, temperature=0.3)

        # Enforce character limits (truncate with warning if exceeded)
        result = _enforce_limits(result, errors)
        result["status"] = "draft"

        logger.info("[marketing] generate_product_hunt_kit — done, tokens=%d", tokens)
        return {
            "product_hunt_kit": result,
            "llm_tokens_used": tokens,
            "errors": errors,
        }
    except Exception as exc:
        err = f"generate_product_hunt_kit: LLM failed: {exc}"
        logger.error("[marketing] %s", err)
        return {
            "product_hunt_kit": {"status": "failed"},
            "errors": [err],
        }


def _enforce_limits(result: dict, errors: list[str]) -> dict:
    """Truncate fields exceeding Product Hunt character limits and warn."""
    for field, limit in [
        ("tagline", _TAGLINE_MAX),
        ("description", _DESCRIPTION_MAX),
        ("first_comment", _FIRST_COMMENT_MAX),
        ("maker_note", _MAKER_NOTE_MAX),
    ]:
        val = result.get(field, "")
        if len(val) > limit:
            logger.warning(
                "[marketing] PH kit: %s exceeded %d chars (%d) — truncating",
                field,
                limit,
                len(val),
            )
            errors.append(f"product_hunt_kit: {field} truncated to {limit} chars")
            result[field] = val[:limit]
    return result
