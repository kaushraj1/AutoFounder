from typing import Any

from jinja2 import Template

from app.agents.strategy.schema import LeanCanvas, StrategistState
from app.agents.strategy.utils.llm_parse import parse_with_correction
from app.agents.strategy.utils.retry import with_retry


@with_retry("synthesize_canvas")
async def synthesize_canvas(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Synthesize a complete 9-box Lean Canvas from the gathered research."""
    raw_template = agent.prompts.get("strategy/synthesize_canvas")
    rendered = Template(raw_template).render(
        idea_normalised=state.idea_normalised,
        market_size=state.market_size.model_dump() if state.market_size else None,
        competitors=[comp.model_dump() for comp in state.competitors],
        personas=[pers.model_dump() for pers in state.personas],
        trend_signals=[sig.model_dump() for sig in state.trend_signals],
        bias_corrections=state.bias_corrections,
    )

    raw_response = await agent._call_llm(
        task_class="synthesize_canvas", prompt=rendered, json_mode=True
    )

    parsed = await parse_with_correction(
        agent=agent,
        task_class="synthesize_canvas",
        raw_output=raw_response,
        schema=LeanCanvas,
        original_prompt=rendered,
    )

    return {
        "lean_canvas": parsed,
    }
