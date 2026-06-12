"""Node 4 — generate_seo_blogs (AF-044).

Generates 3 SEO blog drafts (problem/solution, feature deep-dive, comparison).
Runs in parallel with Nodes 3, 5–8.

Reads:  brand_config, feature_list, brand_voice, seo_keyword_targets,
        competitor_gaps, target_audience_summary, effective_live_url
Writes: seo_blog_drafts
"""

from __future__ import annotations

import logging

from app.agents.marketing.llm import call_llm
from app.agents.marketing.prompt_loader import render
from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)


async def generate_seo_blogs(state: MarketerState) -> MarketerState:
    """LangGraph node: 3 SEO blog drafts (1,500–2,000 words each)."""
    logger.info("[marketing] generate_seo_blogs — start")

    errors: list[str] = list(state.get("errors", []))
    prompt = render(
        "generate_seo_blogs",
        brand_config=state.get("brand_config", {}),
        live_url=state.get("effective_live_url", "[PENDING_DEPLOY]"),
        brand_voice=state.get("brand_voice", ""),
        feature_list=state.get("feature_list", {}),
        target_audience_summary=state.get("target_audience_summary", ""),
        seo_keyword_targets=state.get("seo_keyword_targets", []),
        competitor_gaps=state.get("competitor_gaps", []),
    )

    try:
        result, tokens = await call_llm(prompt, temperature=0.4)
        blogs_raw = result.get("blogs", [])

        # Ensure word_count populated
        blogs: list[dict] = []
        for blog in blogs_raw:
            body = blog.get("body_markdown", "")
            blog["word_count"] = len(body.split())
            blog["status"] = "draft"
            blogs.append(blog)

        logger.info(
            "[marketing] generate_seo_blogs — done, count=%d tokens=%d",
            len(blogs),
            tokens,
        )
        return {
            "seo_blog_drafts": blogs,
            "errors": errors,
            "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
        }
    except Exception as exc:
        err = f"generate_seo_blogs: LLM failed: {exc}"
        logger.error("[marketing] %s", err)
        return {
            "seo_blog_drafts": [],
            "errors": [err],
        }
