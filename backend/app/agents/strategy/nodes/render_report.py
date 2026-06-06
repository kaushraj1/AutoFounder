from typing import Any

from jinja2 import Template

from app.agents.strategy.schema import StrategistState
from app.agents.strategy.utils.retry import with_retry


@with_retry("render_report")
async def render_report(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Render a comprehensive 5-page market analysis report in Markdown."""
    raw_template = agent.prompts.get("strategy/render_report")
    rendered = Template(raw_template).render(
        organization_id=state.organization_id,
        idea_normalised=state.idea_normalised,
        domain=state.domain,
        market_size=state.market_size.model_dump() if state.market_size else None,
        competitors=[comp.model_dump() for comp in state.competitors],
        keywords_top5=[kw.model_dump() for kw in state.keywords[:5]],
        personas=[pers.model_dump() for pers in state.personas],
        trend_signals=[sig.model_dump() for sig in state.trend_signals],
        lean_canvas=state.lean_canvas.model_dump() if state.lean_canvas else None,
        viability_score=state.viability_score.model_dump() if state.viability_score else None,
        viability_score_total=state.viability_score.total if state.viability_score else 0,
        viability_score_band=str(state.viability_score.band) if state.viability_score else "reject",
        bias_flags=[str(flag) for flag in state.bias_flags],
    )

    # Render report directly via model completion
    raw_response = await agent._call_llm(task_class="render_report", prompt=rendered)

    return {
        "report_markdown": raw_response,
    }
