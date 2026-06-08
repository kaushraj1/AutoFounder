from typing import Any

from jinja2 import Template
from pydantic import RootModel

from app.agents.strategy.schema import BuyerPersona, StrategistState
from app.agents.strategy.utils.llm_parse import parse_with_correction
from app.agents.strategy.utils.retry import with_retry


class PersonaListResponse(RootModel[list[BuyerPersona]]):
    pass


@with_retry("generate_personas")
async def generate_personas(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Generate buyer personas using Reddit and search tools to capture buyer pain points."""
    query = f"pain points or problems related to {state.idea_normalised}"

    reddit_results = {}
    try:
        reddit_results = await agent._call_tool("reddit_search", {"query": query})
    except Exception:
        pass

    tool_results = {
        "reddit": reddit_results,
    }

    raw_template = agent.prompts.get("strategy/generate_personas")
    rendered = Template(raw_template).render(
        idea_normalised=state.idea_normalised,
        competitors=[comp.name for comp in state.competitors],
        geography_focus=state.geography_focus,
        tool_results=tool_results,
    )

    raw_response = await agent._call_llm(
        task_class="generate_personas", prompt=rendered, json_mode=True
    )

    parsed = await parse_with_correction(
        agent=agent,
        task_class="generate_personas",
        raw_output=raw_response,
        schema=PersonaListResponse,
        original_prompt=rendered,
    )

    return {
        "personas": parsed.root,
        "total_tool_calls": 1,
    }
