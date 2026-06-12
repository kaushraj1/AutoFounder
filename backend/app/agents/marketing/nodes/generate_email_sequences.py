"""Node 7 — generate_email_sequences (AF-044).

Generates onboarding (Day 0/1/3/7/14) and reactivation (3 emails) drip sequences.
Runs in parallel with Nodes 3–6, 8.

Reads:  brand_config, feature_list, brand_voice, unique_value_proposition,
        target_audience_summary, effective_live_url
Writes: email_sequences
"""

from __future__ import annotations

import logging

from app.agents.marketing.llm import call_llm
from app.agents.marketing.prompt_loader import render
from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)


async def generate_email_sequences(state: MarketerState) -> MarketerState:
    """LangGraph node: onboarding + reactivation email drip sequences."""
    logger.info("[marketing] generate_email_sequences — start")

    errors: list[str] = list(state.get("errors", []))
    prompt = render(
        "generate_email_sequences",
        brand_config=state.get("brand_config", {}),
        live_url=state.get("effective_live_url", "[PENDING_DEPLOY]"),
        brand_voice=state.get("brand_voice", ""),
        unique_value_proposition=state.get("unique_value_proposition", ""),
        target_audience_summary=state.get("target_audience_summary", ""),
        feature_list=state.get("feature_list", {}),
    )

    try:
        result, tokens = await call_llm(prompt, temperature=0.3)
        result["status"] = "draft"

        onboarding = result.get("onboarding", [])
        reactivation = result.get("reactivation", [])

        logger.info(
            "[marketing] generate_email_sequences — done: onboarding=%d reactivation=%d tokens=%d",
            len(onboarding),
            len(reactivation),
            tokens,
        )
        return {
            "email_sequences": result,
            "llm_tokens_used": tokens,
        }
    except Exception as exc:
        err = f"generate_email_sequences: LLM failed: {exc}"
        logger.error("[marketing] %s", err)
        return {
            "email_sequences": {"status": "failed"},
            "errors": [err],
        }
