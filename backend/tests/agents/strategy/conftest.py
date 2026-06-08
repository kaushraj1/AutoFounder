import json
from typing import Any

import pytest

from app.agents._providers import JinjaPromptRegistry
from app.agents.base import ToolRegistryProtocol


class StrategyFakeLLMRouter:
    """Fake LLM Router returning appropriate structured JSON mock content per task class."""

    def __init__(self) -> None:
        self.called_prompts = []
        self.should_fail = False
        self.fail_task_class = None
        self.viability_score_override = None

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        self.called_prompts.append((task_class, prompt))

        if self.should_fail and (
            self.fail_task_class is None or self.fail_task_class == task_class
        ):
            raise Exception(f"LLM failed on {task_class}")

        if task_class == "normalize_idea":
            return json.dumps(
                {
                    "idea_normalised": "Normalized Idea Text",
                    "domain": "B2B SaaS",
                    "geography_focus": "global",
                    "core_problem": "Problem Description",
                    "target_user": "Target User Group",
                }
            )
        elif task_class == "size_market":
            return json.dumps(
                {
                    "tam_usd_bn": 15.0,
                    "sam_usd_bn": 5.0,
                    "som_usd_bn": 1.0,
                    "cagr_pct": 12.5,
                    "sources": ["https://example.com/source"],
                }
            )
        elif task_class == "discover_competitors":
            return json.dumps(
                {
                    "competitors": [
                        {
                            "name": "Competitor Alpha",
                            "url": "https://alpha.com",
                            "funding_usd_mn": 10.0,
                            "employee_range": "employee_range_51_200",
                            "key_features": ["feature 1", "feature 2"],
                            "pricing_model": "freemium",
                            "g2_rating": 4.5,
                            "weakness": "High price",
                        }
                    ],
                    "whitespace": "A clear gap in custom integrations.",
                }
            )
        elif task_class == "mine_keywords":
            return json.dumps(
                [
                    {
                        "term": "best tool",
                        "monthly_search_volume": 1200,
                        "keyword_difficulty": 45,
                        "cpc_usd": 1.5,
                        "intent": "commercial",
                    }
                ]
            )
        elif task_class == "generate_personas":
            return json.dumps(
                [
                    {
                        "name": "Alex",
                        "role": "CTO",
                        "company_size": "50-200",
                        "pain_points": ["scaling API"],
                        "goals": ["reduce latency"],
                        "willingness_to_pay_inr": 8000,
                        "preferred_channels": ["LinkedIn"],
                    }
                ]
            )
        elif task_class == "analyze_trends":
            return json.dumps(
                {
                    "trend_signals": [
                        {
                            "source": "google_trends",
                            "signal": "Rising interest in AI search",
                            "sentiment": "positive",
                            "evidence_url": "https://trends.google.com",
                        }
                    ],
                    "overall_momentum": "accelerating",
                }
            )
        elif task_class == "audit_bias":
            return json.dumps(
                {
                    "bias_flags": ["western_centric"],
                    "bias_notes": {
                        "western_centric": "Sample overrepresented by US tech companies"
                    },
                    "corrections_applied": ["Diversified competitor list"],
                }
            )
        elif task_class == "synthesize_canvas":
            return json.dumps(
                {
                    "problem": ["Problem A", "Problem B"],
                    "customer_segments": ["Segment X", "Segment Y"],
                    "unique_value_proposition": "Best in class custom AI integrations",
                    "solution": ["Solution 1", "Solution 2"],
                    "channels": ["Direct sales"],
                    "revenue_streams": ["SaaS subscriptions"],
                    "cost_structure": ["Cloud hosting"],
                    "key_metrics": ["MRR", "Churn"],
                    "unfair_advantage": "Proprietary validation engine",
                    "early_adopters": "Seed stage startups",
                }
            )
        elif task_class == "score_viability":
            score = self.viability_score_override or 85
            pivots = (
                ["Build vertical API integration", "Target consumer market"] if score < 50 else []
            )
            return json.dumps(
                {
                    "total": score,
                    "breakdown": {
                        "market_size": 18,
                        "competition": 16,
                        "trend": 17,
                        "monetisation": 18,
                        "feasibility": 16,
                    },
                    "pivot_suggestions": pivots,
                }
            )
        elif task_class == "render_report":
            return "## Page 1 — Executive Summary\nReport Body..."

        return "default"


class StrategyFakeToolRegistry(ToolRegistryProtocol):
    """Fake Tool Registry returning successful mock data instead of calling raw APIs."""

    def __init__(self) -> None:
        self.called_tools = []
        self.should_fail = False

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        self.called_tools.append((tool_name, args))
        if self.should_fail:
            raise Exception(f"Tool {tool_name} failed")

        if tool_name == "tavily_search":
            return {
                "results": [
                    {
                        "title": "Search Result",
                        "url": "https://example.com/res",
                        "content": "Sample content",
                    }
                ]
            }
        elif tool_name == "serp_search":
            return {"results": [{"title": "Google Search Result", "snippet": "Sample snippet"}]}
        elif tool_name == "crunchbase_lookup":
            return {"funding_total": 12.0, "num_employees_enum": "employee_range_51_200"}
        elif tool_name == "g2_reviews":
            return {"g2_rating": 4.6}
        elif tool_name == "google_trends":
            return {"trend_direction": "up"}
        elif tool_name == "reddit_search":
            return {"posts": [{"title": "Reddit thread", "body": "Need API tool"}]}
        elif tool_name == "hn_search":
            return {"hits": [{"title": "HN thread", "points": 100}]}
        return {}


@pytest.fixture
def fake_llm() -> StrategyFakeLLMRouter:
    return StrategyFakeLLMRouter()


@pytest.fixture
def fake_tools() -> StrategyFakeToolRegistry:
    return StrategyFakeToolRegistry()


@pytest.fixture
def local_prompts() -> JinjaPromptRegistry:
    return JinjaPromptRegistry()


@pytest.fixture
def mock_udal() -> Any:
    # A dummy mock UDAL object
    class DummyUDAL:
        def __init__(self):
            self.organization_id = "org_123"

    return DummyUDAL()
