"""Node 3 — generate_landing_page (AF-044).

Generates full landing page copy grounded in the FeatureList.
Runs in parallel with Nodes 4–8.

Reads:  brand_config, feature_list, brand_voice, positioning_statement,
        unique_value_proposition, seo_keyword_targets, effective_live_url, target_audience_summary
Writes: landing_page
"""

from __future__ import annotations

import logging

from app.agents.marketing.llm import call_llm
from app.agents.marketing.prompt_loader import render
from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)


async def generate_landing_page(state: MarketerState) -> MarketerState:
    """LangGraph node: full landing page copy + meta tags."""
    logger.info("[marketing] generate_landing_page — start")

    errors: list[str] = list(state.get("errors", []))
    prompt = render(
        "generate_landing_page",
        brand_config=state.get("brand_config", {}),
        live_url=state.get("effective_live_url", "[PENDING_DEPLOY]"),
        brand_voice=state.get("brand_voice", ""),
        positioning_statement=state.get("positioning_statement", ""),
        unique_value_proposition=state.get("unique_value_proposition", ""),
        target_audience_summary=state.get("target_audience_summary", ""),
        feature_list=state.get("feature_list", {}),
        seo_keyword_targets=state.get("seo_keyword_targets", []),
    )

    try:
        result, tokens = await call_llm(prompt, temperature=0.3)
        result["status"] = "draft"
        logger.info("[marketing] generate_landing_page — done, tokens=%d", tokens)
        return {
            "landing_page": result,
            "errors": errors,
            "llm_tokens_used": tokens,
        }
    except Exception as exc:
        err = f"generate_landing_page: LLM failed: {exc}"
        logger.error("[marketing] %s", err)
        return {
            "landing_page": _empty_landing_page(state),
            "errors": errors + [err],
        }


def _empty_landing_page(state: MarketerState) -> dict:
    brand = state.get("brand_config", {})
    url = state.get("effective_live_url", "[PENDING_DEPLOY]")
    return {
        "hero_headline": brand.get("tagline", ""),
        "hero_subheadline": state.get("unique_value_proposition", ""),
        "hero_cta_text": "Get Started",
        "hero_cta_url": url,
        "features_section": [],
        "social_proof_section": "",
        "pricing_section": [],
        "faq_section": [],
        "cta_footer_text": "",
        "meta_tags": None,
        "status": "draft_empty",
    }
