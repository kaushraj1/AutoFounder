from typing import Any

from jinja2 import Template
from pydantic import RootModel

from app.agents.strategy.schema import Keyword, StrategistState
from app.agents.strategy.utils.llm_parse import parse_with_correction
from app.agents.strategy.utils.retry import with_retry


class KeywordListResponse(RootModel[list[Keyword]]):
    pass


@with_retry("mine_keywords")
async def mine_keywords(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Mine high-value search terms and difficulty using SerpAPI."""
    query = f"{state.idea_normalised} SEO keywords search volumes"

    serp_results = {}
    try:
        serp_results = await agent._call_tool("serp_search", {"query": query})
    except Exception:
        pass

    tool_results = {
        "serp": serp_results,
    }

    raw_template = agent.prompts.get("strategy/mine_keywords")
    rendered = Template(raw_template).render(
        idea_normalised=state.idea_normalised,
        domain=state.domain,
        tool_results=tool_results,
    )

    raw_response = await agent._call_llm(
        task_class="mine_keywords", prompt=rendered, json_mode=True
    )

    parsed = await parse_with_correction(
        agent=agent,
        task_class="mine_keywords",
        raw_output=raw_response,
        schema=KeywordListResponse,
        original_prompt=rendered,
    )

    return {
        "keywords": parsed.root,
        "total_tool_calls": 1,
    }
