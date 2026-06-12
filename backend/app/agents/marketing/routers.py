"""Conditional edge routers for the Marketing Agent StateGraph (AF-044).

Each router function is passed the current state and returns a string key
that LangGraph uses to select the next node.
"""

from __future__ import annotations

import logging

from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)

_MAX_HALLUCINATION_RETRIES = 2


def route_after_ingest(state: MarketerState) -> str:
    """Route after ingest_input.

    Returns:
        "analyse_brand" — normal path
        "error_handler" — fatal error (e.g. empty feature_list)
    """
    if state.get("fatal_error"):
        logger.error("[marketing] router: ingest → error_handler (fatal=%s)", state["fatal_error"])
        return "error_handler"
    return "analyse_brand"


def route_after_hallucination(state: MarketerState) -> str:
    """Route after hallucination_check.

    Returns:
        "launch_control_center" — passed (critical_count == 0)
        "generate_landing_page" — failed but retries remaining (re-generate)
        "error_handler"         — retries exhausted
    """
    passed = state.get("hallucination_passed", False)
    retry_count = state.get("hallucination_retry_count", 0)

    if passed:
        logger.info("[marketing] router: hallucination → launch_control_center (passed)")
        return "launch_control_center"

    if retry_count < _MAX_HALLUCINATION_RETRIES:
        logger.warning(
            "[marketing] router: hallucination → regenerate (retry=%d/%d)",
            retry_count + 1,
            _MAX_HALLUCINATION_RETRIES,
        )
        # Increment retry count in state for the next hallucination_check pass
        state["hallucination_retry_count"] = retry_count + 1  # type: ignore[literal-required]
        return "generate_landing_page"  # re-runs all 6 generators via fan-out

    logger.error(
        "[marketing] router: hallucination → error_handler (retries exhausted after %d attempts)",
        retry_count,
    )
    return "error_handler"


def route_after_hitl(state: MarketerState) -> str:
    """Route after launch_control_center.

    Returns:
        "schedule_posts" — approved or partial
        "error_handler"  — rejected or timed_out
    """
    status = state.get("approval_status", "pending")

    if status in ("approved", "partial"):
        logger.info("[marketing] router: hitl → schedule_posts (status=%s)", status)
        return "schedule_posts"

    if status == "timed_out":
        logger.warning("[marketing] router: hitl → error_handler (timed_out)")
        return "error_handler"

    # rejected
    logger.warning("[marketing] router: hitl → error_handler (rejected)")
    return "error_handler"
