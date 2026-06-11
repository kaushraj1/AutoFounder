"""Node 7 — compose_featurelist (AF-040).  CRITICAL output.

Reads: lean_canvas, requirements[], stack, openapi_3_1, microservice_boundaries
Writes: feature_list{}  (FeatureList — ground truth for Pillar 3 + Pillar 6)
"""

from __future__ import annotations

import logging

from app.agents.architect.llm import call_llm
from app.agents.architect.prompt_loader import render
from app.agents.architect.state import ArchitectState

logger = logging.getLogger(__name__)


def compose_featurelist(state: ArchitectState) -> ArchitectState:
    """LangGraph node: compose the canonical FeatureList."""
    logger.info("[architect] compose_featurelist — start")

    # Extract path keys from the OpenAPI spec to ground the FeatureList
    openapi = state.get("openapi_3_1") or {}
    openapi_paths: list[str] = list(openapi.get("paths", {}).keys())

    prompt = render(
        "compose_featurelist",
        lean_canvas=state.get("lean_canvas", {}),
        requirements=state.get("requirements", []),
        stack=state.get("stack", {}),
        openapi_paths=openapi_paths,
        microservice_boundaries=state.get("microservice_boundaries", []),
    )

    result, tokens = call_llm(prompt)

    features: list[str] = result.get("features", [])
    integrations: list[str] = result.get("integrations", [])
    pricing_tiers: list[dict] = result.get("pricing_tiers", [])

    errors = list(state.get("errors", []))

    # FATAL guard — Pillar 6 refuses to run without features
    if not features:
        msg = "compose_featurelist: FeatureList.features is EMPTY — FATAL for Pillar 6"
        logger.error("[architect] %s", msg)
        errors.append(msg)

    logger.info(
        "[architect] compose_featurelist — %d features, %d integrations, %d tiers",
        len(features),
        len(integrations),
        len(pricing_tiers),
    )

    return {
        **state,
        "feature_list": {
            "features": features,
            "integrations": integrations,
            "pricing_tiers": pricing_tiers,
        },
        "errors": errors,
        "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
    }
