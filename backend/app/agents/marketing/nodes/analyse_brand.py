"""Node 2 — analyse_brand (AF-044).

Uses Tavily + Ahrefs + Gemini to produce brand voice, positioning,
SEO keyword targets, and competitor gap analysis.

Reads:  idea_normalised, brand_config, feature_list, lean_canvas_json, personas
Writes: brand_voice, positioning_statement, unique_value_proposition,
        seo_keyword_targets, competitor_gaps, target_audience_summary
"""

from __future__ import annotations

import logging

from app.agents.marketing.llm import call_llm
from app.agents.marketing.prompt_loader import render
from app.agents.marketing.state import MarketerState
from app.agents.marketing.tools.tavily_search import tavily_search

logger = logging.getLogger(__name__)


async def analyse_brand(state: MarketerState) -> MarketerState:
    """LangGraph node: brand voice, positioning, SEO keyword strategy."""
    logger.info("[marketing] analyse_brand — start")

    brand_config = state.get("brand_config", {})
    feature_list = state.get("feature_list", {})
    product_name = brand_config.get("product_name", "")
    errors: list[str] = list(state.get("errors", []))

    # ---- 1. Optional: Tavily competitor research ----
    tavily_data: dict = {}
    if product_name:
        query = f"{product_name} competitors alternatives {state.get('idea_normalised', '')}"
        tavily_data = await tavily_search(query, max_results=5)
        if tavily_data.get("fallback"):
            logger.info("[marketing] analyse_brand — using LLM knowledge (Tavily unavailable)")

    # ---- 2. Build prompt ----
    prompt = render(
        "analyse_brand",
        brand_config=brand_config,
        idea_normalised=state.get("idea_normalised", ""),
        lean_canvas_json=state.get("lean_canvas_json", {}),
        feature_list=feature_list,
        personas=state.get("personas", []),
    )

    # ---- 3. LLM call ----
    try:
        result, tokens = await call_llm(prompt)
    except Exception as exc:
        err = f"analyse_brand: LLM failed: {exc}"
        logger.error("[marketing] %s", err)
        return {
            **state,
            "brand_voice": f"{brand_config.get('tone', 'professional')} brand voice",
            "positioning_statement": f"{product_name} — {state.get('idea_normalised', '')}",
            "unique_value_proposition": brand_config.get("tagline", ""),
            "seo_keyword_targets": [],
            "competitor_gaps": [],
            "target_audience_summary": brand_config.get("target_audience", ""),
            "errors": errors + [err],
            "llm_tokens_used": state.get("llm_tokens_used", 0),
        }

    # ---- 4. Extract keyword strings from structured response ----
    raw_keywords = result.get("seo_keyword_targets", [])
    keyword_strings: list[str] = []
    for kw in raw_keywords:
        if isinstance(kw, dict):
            keyword_strings.append(kw.get("keyword", ""))
        elif isinstance(kw, str):
            keyword_strings.append(kw)

    logger.info(
        "[marketing] analyse_brand — done, keywords=%d tokens=%d",
        len(keyword_strings),
        tokens,
    )

    return {
        **state,
        "brand_voice": result.get("brand_voice", ""),
        "positioning_statement": result.get("positioning_statement", ""),
        "unique_value_proposition": result.get("unique_value_proposition", ""),
        "seo_keyword_targets": keyword_strings,
        "competitor_gaps": result.get("competitor_gaps", []),
        "target_audience_summary": result.get("target_audience_summary", ""),
        "errors": errors,
        "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
    }
