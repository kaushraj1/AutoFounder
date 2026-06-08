from typing import Any

from jinja2 import Template
from pydantic import BaseModel, Field

from app.agents.strategy.schema import BiasFlag, StrategistState
from app.agents.strategy.utils.llm_parse import parse_with_correction
from app.agents.strategy.utils.retry import with_retry


class BiasAuditResponse(BaseModel):
    bias_flags: list[BiasFlag] = Field(default_factory=list)
    bias_notes: dict[str, str] = Field(default_factory=dict)
    corrections_applied: list[str] = Field(default_factory=list)


@with_retry("audit_bias")
async def audit_bias(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Audit the accumulated research files for confirmation and demographic bias."""
    raw_template = agent.prompts.get("strategy/audit_bias")
    rendered = Template(raw_template).render(
        market_size=state.market_size.model_dump() if state.market_size else None,
        competitors=[comp.model_dump() for comp in state.competitors],
        geography_focus=state.geography_focus,
        trend_signals=[sig.model_dump() for sig in state.trend_signals],
    )

    raw_response = await agent._call_llm(task_class="audit_bias", prompt=rendered, json_mode=True)

    parsed = await parse_with_correction(
        agent=agent,
        task_class="audit_bias",
        raw_output=raw_response,
        schema=BiasAuditResponse,
        original_prompt=rendered,
    )

    return {
        "bias_flags": parsed.bias_flags,
        "bias_corrections": parsed.corrections_applied,
    }
