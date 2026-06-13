"""Node 1 — ingest_input (AF-044).

Validates all required inputs before any generation begins.
FATAL if feature_list is empty — hallucinaton prevention.

Reads:  live_url, feature_list, brand_config, idea_normalised
Writes: validated, effective_live_url, fatal_error
"""

from __future__ import annotations

import logging

from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)

_PLACEHOLDER_URL = "[PENDING_DEPLOY]"


async def ingest_input(state: MarketerState) -> MarketerState:
    """LangGraph node: validate inputs; FATAL if feature_list missing/empty."""
    logger.info("[marketing] ingest_input — start run_id=%s", state.get("run_id"))

    errors: list[str] = list(state.get("errors", []))
    fatal_error: str | None = None

    # ---- 1. Feature list is MANDATORY (hallucination prevention) ----
    feature_list = state.get("feature_list", {})
    features = feature_list.get("features", [])
    if not features:
        fatal_error = (
            "ingest_input: feature_list.features is empty — "
            "FATAL: marketing generation refused without ground truth"
        )
        logger.error("[marketing] %s", fatal_error)
        return {
            **state,
            "validated": False,
            "fatal_error": fatal_error,
            "errors": errors + [fatal_error],
        }

    # ---- 2. Brand config must have product_name ----
    brand_config = state.get("brand_config", {})
    if not brand_config.get("product_name"):
        fatal_error = "ingest_input: brand_config.product_name is required"
        logger.error("[marketing] %s", fatal_error)
        return {
            **state,
            "validated": False,
            "fatal_error": fatal_error,
            "errors": errors + [fatal_error],
        }

    # ---- 3. live_url — soft dependency, placeholder if missing ----
    live_url = (state.get("live_url") or "").strip()
    if not live_url:
        effective_live_url = _PLACEHOLDER_URL
        logger.warning(
            "[marketing] ingest_input — live_url empty, using placeholder %s",
            _PLACEHOLDER_URL,
        )
        errors = errors + [f"live_url empty — CTAs will use {_PLACEHOLDER_URL}"]
    else:
        effective_live_url = live_url

    # ---- 4. idea_normalised — soft dependency ----
    if not state.get("idea_normalised"):
        logger.warning("[marketing] ingest_input — idea_normalised empty")
        errors = errors + ["idea_normalised empty — brand analysis may be generic"]

    logger.info(
        "[marketing] ingest_input — validated OK: features=%d url=%s",
        len(features),
        effective_live_url,
    )

    return {
        **state,
        "validated": True,
        "fatal_error": None,
        "effective_live_url": effective_live_url,
        "errors": errors,
    }
