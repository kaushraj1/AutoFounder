from typing import Any

from jinja2 import Template

from app.agents.strategy.schema import StrategistState, ViabilityScore
from app.agents.strategy.utils.llm_parse import parse_with_correction
from app.agents.strategy.utils.retry import with_retry


@with_retry("score_viability")
async def score_viability(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Score the overall startup idea viability and derive the band."""
    raw_template = agent.prompts.get("strategy/score_viability")
    rendered = Template(raw_template).render(
        lean_canvas=state.lean_canvas.model_dump() if state.lean_canvas else None,
        market_size=state.market_size.model_dump() if state.market_size else None,
        competitors=[comp.model_dump() for comp in state.competitors],
        overall_momentum=state.overall_momentum or "stable",
        bias_flags=[str(flag) for flag in state.bias_flags],
    )

    raw_response = await agent._call_llm(
        task_class="score_viability", prompt=rendered, json_mode=True
    )

    parsed = await parse_with_correction(
        agent=agent,
        task_class="score_viability",
        raw_output=raw_response,
        schema=ViabilityScore,
        original_prompt=rendered,
    )

    return {
        "viability_score": parsed,
    }
