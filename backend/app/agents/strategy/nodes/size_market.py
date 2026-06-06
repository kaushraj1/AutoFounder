from typing import Any

from jinja2 import Template

from app.agents.strategy.schema import MarketSize, StrategistState
from app.agents.strategy.utils.llm_parse import parse_with_correction
from app.agents.strategy.utils.retry import with_retry


@with_retry("size_market")
async def size_market(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Gather and size the TAM / SAM / SOM from market research tools."""
    query = (
        f"{state.domain} {state.idea_normalised} market size TAM SAM SOM "
        f"geography focus {state.geography_focus}"
    )

    tavily_results = {}
    try:
        tavily_results = await agent._call_tool("tavily_search", {"query": query})
    except Exception:
        pass

    serp_results = {}
    try:
        serp_results = await agent._call_tool("serp_search", {"query": query})
    except Exception:
        pass

    tool_results = {
        "tavily": tavily_results,
        "serp": serp_results,
    }

    raw_template = agent.prompts.get("strategy/size_market")
    rendered = Template(raw_template).render(
        idea_normalised=state.idea_normalised,
        domain=state.domain,
        geography_focus=state.geography_focus,
        tool_results=tool_results,
    )

    raw_response = await agent._call_llm(task_class="size_market", prompt=rendered, json_mode=True)

    parsed = await parse_with_correction(
        agent=agent,
        task_class="size_market",
        raw_output=raw_response,
        schema=MarketSize,
        original_prompt=rendered,
    )

    return {
        "market_size": parsed,
        "total_tool_calls": 2,
    }
