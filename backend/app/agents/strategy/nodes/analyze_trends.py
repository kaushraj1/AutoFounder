from typing import Any

from jinja2 import Template
from pydantic import BaseModel

from app.agents.strategy.schema import StrategistState, TrendSignal
from app.agents.strategy.utils.llm_parse import parse_with_correction
from app.agents.strategy.utils.retry import with_retry


class TrendsResponse(BaseModel):
    trend_signals: list[TrendSignal]
    overall_momentum: str


@with_retry("analyze_trends")
async def analyze_trends(state: StrategistState, agent: Any) -> dict[str, Any]:
    """Analyze Google Trends and community forums to extract signals and momentum."""
    term = state.idea_normalised or "startup"

    google_trends = {}
    try:
        google_trends = await agent._call_tool("google_trends", {"keyword": term})
    except Exception:
        pass

    reddit_search = {}
    try:
        reddit_search = await agent._call_tool("reddit_search", {"query": term})
    except Exception:
        pass

    hn_search = {}
    try:
        hn_search = await agent._call_tool("hn_search", {"query": term})
    except Exception:
        pass

    raw_template = agent.prompts.get("strategy/analyze_trends")
    rendered = Template(raw_template).render(
        idea_normalised=state.idea_normalised,
        google_trends=google_trends,
        reddit_search=reddit_search,
        hn_search=hn_search,
    )

    raw_response = await agent._call_llm(
        task_class="analyze_trends", prompt=rendered, json_mode=True
    )

    parsed = await parse_with_correction(
        agent=agent,
        task_class="analyze_trends",
        raw_output=raw_response,
        schema=TrendsResponse,
        original_prompt=rendered,
    )

    return {
        "trend_signals": parsed.trend_signals,
        "overall_momentum": parsed.overall_momentum,
        "total_tool_calls": 3,
    }
