"""Node 6 — generate_social_posts (AF-044).

Generates X thread (4–6 tweets), LinkedIn long-form, and Show HN post.
Runs in parallel with Nodes 3–5, 7–8.

Reads:  brand_config, feature_list, brand_voice, unique_value_proposition,
        positioning_statement, target_audience_summary, effective_live_url
Writes: social_post_bundle
"""

from __future__ import annotations

import logging

from app.agents.marketing.llm import call_llm
from app.agents.marketing.prompt_loader import render
from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)

_TWEET_MAX_CHARS = 280


async def generate_social_posts(state: MarketerState) -> MarketerState:
    """LangGraph node: X thread, LinkedIn post, Show HN post."""
    logger.info("[marketing] generate_social_posts — start")

    errors: list[str] = list(state.get("errors", []))
    prompt = render(
        "generate_social_posts",
        brand_config=state.get("brand_config", {}),
        live_url=state.get("effective_live_url", "[PENDING_DEPLOY]"),
        brand_voice=state.get("brand_voice", ""),
        unique_value_proposition=state.get("unique_value_proposition", ""),
        positioning_statement=state.get("positioning_statement", ""),
        target_audience_summary=state.get("target_audience_summary", ""),
        feature_list=state.get("feature_list", {}),
    )

    try:
        result, tokens = await call_llm(prompt, temperature=0.4)

        # Validate tweet lengths
        x_thread = result.get("x_thread", [])
        validated_tweets: list[str] = []
        for i, tweet in enumerate(x_thread):
            if len(tweet) > _TWEET_MAX_CHARS:
                logger.warning(
                    "[marketing] social_posts: tweet %d exceeds 280 chars (%d) — truncating",
                    i + 1,
                    len(tweet),
                )
                errors.append(f"social_posts: tweet {i + 1} truncated to 280 chars")
                tweet = tweet[:_TWEET_MAX_CHARS]
            validated_tweets.append(tweet)

        result["x_thread"] = validated_tweets
        result["status"] = "draft"

        logger.info("[marketing] generate_social_posts — done, tokens=%d", tokens)
        return {
            "social_post_bundle": result,
            "llm_tokens_used": tokens,
        }
    except Exception as exc:
        err = f"generate_social_posts: LLM failed: {exc}"
        logger.error("[marketing] %s", err)
        return {
            "social_post_bundle": {"status": "failed"},
            "errors": [err],
        }
