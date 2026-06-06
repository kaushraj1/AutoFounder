from typing import Any

from jinja2 import Template
from pydantic import BaseModel

from app.agents.strategy.schema import StrategistState
from app.agents.strategy.utils.llm_parse import parse_with_correction
from app.agents.strategy.utils.retry import with_retry


class NormalizeResponse(BaseModel):
    idea_normalised: str
    domain: str
    geography_focus: str
    core_problem: str
    target_user: str


@with_retry("normalize_idea")
async def normalize_idea(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Normalize the raw user idea text using Gemini."""
    raw_template = agent.prompts.get("strategy/normalize_idea")
    rendered = Template(raw_template).render(idea_raw=state.idea_raw)
    raw_response = await agent._call_llm(
        task_class="normalize_idea", prompt=rendered, json_mode=True
    )
    parsed = await parse_with_correction(
        agent=agent,
        task_class="normalize_idea",
        raw_output=raw_response,
        schema=NormalizeResponse,
        original_prompt=rendered,
    )
    return {
        "idea_normalised": parsed.idea_normalised,
        "domain": parsed.domain,
        "geography_focus": parsed.geography_focus,
    }
