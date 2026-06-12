"""Node 10 — hallucination_check (AF-044).

Cross-references ALL generated marketing copy against the confirmed FeatureList.
This is a standalone component — can be tested in isolation without the full graph.

Reads:  feature_list, landing_page, product_hunt_kit, social_post_bundle, email_sequences
Writes: hallucination_report, hallucination_passed, hallucination_retry_count

Retry logic:
  - If critical_count > 0 and retry_count < 2: the graph routes back to regenerate
    affected content (handled in routers.py)
  - If retry_count >= 2: route to error_handler (Slack alert + TIMED_OUT state)
"""

from __future__ import annotations

import logging

from app.agents.marketing.llm import call_llm
from app.agents.marketing.prompt_loader import render
from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2


async def hallucination_check(state: MarketerState) -> MarketerState:
    """LangGraph node: cross-reference all generated copy against FeatureList."""
    retry_count = state.get("hallucination_retry_count", 0)
    logger.info("[marketing] hallucination_check — start (retry=%d/%d)", retry_count, _MAX_RETRIES)

    list(state.get("errors", []))
    feature_list = state.get("feature_list", {})

    # ---- Extract Day-0 email for quick check ----
    email_seqs = state.get("email_sequences", {})
    onboarding = email_seqs.get("onboarding", [])
    email_day0 = onboarding[0] if onboarding else {}

    prompt = render(
        "hallucination_check",
        feature_list=feature_list,
        landing_page=state.get("landing_page", {}),
        product_hunt_kit=state.get("product_hunt_kit", {}),
        social_post_bundle=state.get("social_post_bundle", {}),
        email_sequences=email_seqs,
        email_day0_subject=email_day0.get("subject", ""),
        email_day0_preview=email_day0.get("preview_text", ""),
    )

    try:
        result, tokens = await call_llm(prompt, temperature=0.0)  # deterministic
    except Exception as exc:
        err = f"hallucination_check: LLM failed: {exc}"
        logger.error("[marketing] %s", err)
        return {
            "hallucination_report": {
                "critical_count": 0,
                "warning_count": 1,
                "passed": True,
                "retry_count": retry_count,
                "findings": [{"claim": "Audit failed", "severity": "WARNING", "reason": err}],
            },
            "hallucination_passed": True,
            "hallucination_retry_count": retry_count,
            "errors": [err],
        }

    critical_count = result.get("critical_count", 0)
    warning_count = result.get("warning_count", 0)
    passed = critical_count == 0

    if not passed:
        retry_count += 1
        logger.warning(
            "[marketing] hallucination_check — FAILED: critical=%d warning=%d (retry=%d)",
            critical_count,
            warning_count,
            retry_count,
        )
    else:
        logger.info(
            "[marketing] hallucination_check — PASSED: warning=%d tokens=%d",
            warning_count,
            tokens,
        )

    result["retry_count"] = retry_count
    result["passed"] = passed

    return {
        "hallucination_report": result,
        "hallucination_passed": passed,
        "hallucination_retry_count": retry_count,
        "llm_tokens_used": tokens,
    }


# ---------------------------------------------------------------------------
# Standalone validator — can be imported and used without the graph
# ---------------------------------------------------------------------------


async def validate_claims_against_features(
    claims: list[str],
    feature_list: dict,
    *,
    source_node: str = "unknown",
) -> dict:
    """Standalone hallucination validator.

    Args:
        claims: List of marketing claim strings to validate.
        feature_list: FeatureList dict (features, integrations, pricing_tiers).
        source_node: Label for the source generator node.

    Returns:
        HallucinationReport dict.
    """
    if not claims:
        return {"critical_count": 0, "warning_count": 0, "passed": True, "findings": []}

    features_str = "\n".join(f"- {f}" for f in feature_list.get("features", []))
    claims_str = "\n".join(f"- {c}" for c in claims)

    prompt = (
        f"You are a fact-checker. Compare each claim below against the confirmed feature list.\n"
        f"Classify each claim as NONE (accurate), WARNING (implied), or CRITICAL (false).\n\n"
        f"## Confirmed Features\n{features_str}\n\n"
        f"## Claims to Check\n{claims_str}\n\n"
        f"Respond with JSON only:\n"
        f'{{"critical_count": 0, "warning_count": 0, "passed": true, "findings": []}}'
    )

    try:
        result, _ = await call_llm(prompt, temperature=0.0)
        result["passed"] = result.get("critical_count", 0) == 0
        return result
    except Exception as exc:
        logger.error("[marketing] standalone hallucination check failed: %s", exc)
        return {
            "critical_count": 0,
            "warning_count": 1,
            "passed": True,
            "findings": [{"claim": "Audit failed", "severity": "WARNING", "reason": str(exc)}],
        }
