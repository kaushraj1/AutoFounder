"""Node 6 — cost_forecast (AF-040).

Reads: stack, scaling_plan
Writes: cost_estimate{}, pricing_source
"""

from __future__ import annotations

import logging

from app.agents.architect.llm import call_llm
from app.agents.architect.prompt_loader import render
from app.agents.architect.state import ArchitectState
from app.agents.architect.tools.aws_pricing import AWSPricingTool

logger = logging.getLogger(__name__)
_pricing_tool = AWSPricingTool()


def cost_forecast(state: ArchitectState) -> ArchitectState:
    """LangGraph node: produce a 3-tier AWS cost forecast."""
    logger.info("[architect] cost_forecast — fetching pricing data")

    pricing_result = _pricing_tool.get_prices()
    logger.info("[architect] cost_forecast — pricing source: %s", pricing_result.source)

    prompt = render(
        "cost_forecast",
        stack=state.get("stack", {}),
        scaling_plan=state.get("scaling_plan", {}),
        pricing_data=pricing_result.data,
        pricing_source=pricing_result.source,
    )

    result, tokens = call_llm(prompt)

    # If static fallback was used, ensure is_estimate is True
    if pricing_result.source == "static_fallback":
        result["is_estimate"] = True

    startup_cost = result.get("tiers", {}).get("startup", {}).get("monthly_usd", 0)
    logger.info(
        "[architect] cost_forecast — startup tier: $%.2f/mo (estimate=%s)",
        startup_cost,
        result.get("is_estimate", False),
    )

    return {
        **state,
        "cost_estimate": result,
        "pricing_source": pricing_result.source,
        "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
    }
