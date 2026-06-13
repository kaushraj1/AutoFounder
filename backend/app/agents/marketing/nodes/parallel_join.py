"""Node 9 — parallel_join (AF-044).

Barrier node — waits for all 6 parallel generators to complete, then merges.
Performs graceful soft-fail: logs which generators failed but does NOT abort.

Reads:  landing_page, seo_blog_drafts, product_hunt_kit, social_post_bundle,
        email_sequences, visual_asset_bundle
Writes: parallel_complete, generators_completed, generators_failed
"""

from __future__ import annotations

import logging

from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)

_GENERATOR_FIELDS = {
    "landing_page": "landing_page",
    "seo_blogs": "seo_blog_drafts",
    "product_hunt_kit": "product_hunt_kit",
    "social_posts": "social_post_bundle",
    "email_sequences": "email_sequences",
    "visual_assets": "visual_asset_bundle",
}


async def parallel_join(state: MarketerState) -> MarketerState:
    """LangGraph node: barrier — verify all 6 generators have written output."""
    logger.info("[marketing] parallel_join — checking generator outputs")

    completed: list[str] = []
    failed: list[str] = []
    errors: list[str] = list(state.get("errors", []))

    for name, field in _GENERATOR_FIELDS.items():
        value = state.get(field)
        if value:
            completed.append(name)
        else:
            failed.append(name)
            errors.append(f"parallel_join: generator '{name}' produced no output")
            logger.warning("[marketing] parallel_join: generator '%s' has no output", name)

    logger.info(
        "[marketing] parallel_join — completed=%d failed=%d",
        len(completed),
        len(failed),
    )

    return {
        **state,
        "parallel_complete": True,
        "generators_completed": completed,
        "generators_failed": failed,
        "errors": errors,
    }
