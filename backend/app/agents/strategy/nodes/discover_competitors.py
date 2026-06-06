from typing import Any

from jinja2 import Template
from pydantic import BaseModel, Field

from app.agents.strategy.schema import Competitor, StrategistState
from app.agents.strategy.utils.llm_parse import parse_with_correction
from app.agents.strategy.utils.retry import with_retry


class CompetitorsResponse(BaseModel):
    competitors: list[Competitor] = Field(default_factory=list)
    whitespace: str


@with_retry("discover_competitors")
async def discover_competitors(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Identify direct competitors and fetch additional metadata using tools."""
    query = f"top direct competitors and alternatives to {state.idea_normalised} in {state.domain}"

    tavily_results = {}
    try:
        tavily_results = await agent._call_tool("tavily_search", {"query": query})
    except Exception:
        pass

    tool_results = {
        "tavily": tavily_results,
    }

    raw_template = agent.prompts.get("strategy/discover_competitors")
    rendered = Template(raw_template).render(
        idea_normalised=state.idea_normalised,
        domain=state.domain,
        tool_results=tool_results,
    )

    raw_response = await agent._call_llm(
        task_class="discover_competitors", prompt=rendered, json_mode=True
    )

    parsed = await parse_with_correction(
        agent=agent,
        task_class="discover_competitors",
        raw_output=raw_response,
        schema=CompetitorsResponse,
        original_prompt=rendered,
    )

    enriched_competitors = []
    tool_calls_made = 1

    # Enrich up to 3 competitors to stay within rate limits and SLA
    for comp in parsed.competitors[:3]:
        cb_res = None
        try:
            cb_res = await agent._call_tool("crunchbase_lookup", {"company_name": comp.name})
            tool_calls_made += 1
        except Exception:
            pass

        g2_res = None
        try:
            g2_res = await agent._call_tool("g2_reviews", {"product_name": comp.name})
            tool_calls_made += 1
        except Exception:
            pass

        if cb_res:
            comp.funding_usd_mn = cb_res.get("funding_total", comp.funding_usd_mn)
            comp.employee_range = cb_res.get("num_employees_enum", comp.employee_range)
        if g2_res:
            comp.g2_rating = g2_res.get("g2_rating", comp.g2_rating)

        enriched_competitors.append(comp)

    # Append any remaining without enrichment
    for comp in parsed.competitors[3:]:
        enriched_competitors.append(comp)

    return {
        "competitors": enriched_competitors,
        "total_tool_calls": tool_calls_made,
    }
