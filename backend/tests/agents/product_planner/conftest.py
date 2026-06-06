"""Shared fixtures for Product Planner Agent tests."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.base import ToolRegistryProtocol
from app.agents.product_planner.schema import (
    PRD,
    Milestone,
    ProductPlannerInput,
    ProductPlannerOutput,
    Requirement,
    UserStory,
)
from app.agents.strategy.schema import (
    BuyerPersona,
    Competitor,
    LeanCanvas,
    StrategyOutput,
)

# ---------------------------------------------------------------------------
# Fake LLM router — returns canned staged JSON keyed by call order
# ---------------------------------------------------------------------------

_FAKE_PRD = {
    "title": "TeamSync",
    "overview": "AI-powered scheduling for remote teams.",
    "problem_statement": "Remote teams waste hours coordinating across time zones.",
    "goals": ["Reduce scheduling friction by 80%", "Increase meeting attendance"],
    "non_goals": ["Replace video conferencing"],
    "target_users": ["Alex Chen"],
    "success_metrics": ["50% fewer scheduling emails", "NPS > 40"],
    "scope_in": ["Smart calendar integration", "Timezone auto-detection"],
    "scope_out": ["Video calls"],
}

_FAKE_REQUIREMENTS = [
    {
        "id": "FR-001",
        "kind": "functional",
        "statement": "System shall sync calendars across Google, Outlook, and iCal.",
        "priority": "must",
        "rationale": "Core scheduling capability.",
        "traces_to": "Smart calendar integration",
    },
    {
        "id": "FR-002",
        "kind": "functional",
        "statement": "System shall detect participant time zones automatically.",
        "priority": "must",
        "rationale": "Eliminates manual timezone lookup.",
        "traces_to": "Timezone auto-detection",
    },
    {
        "id": "NFR-001",
        "kind": "non_functional",
        "statement": "Calendar sync shall complete within 2 seconds for teams up to 50 members.",
        "priority": "must",
        "rationale": "Performance NFR.",
        "traces_to": "Smart calendar integration",
    },
]

_FAKE_USER_STORIES = [
    {
        "id": "US-001",
        "persona": "Alex Chen",
        "role": "Engineering Manager",
        "want": "sync my calendar automatically",
        "benefit": "I never miss a cross-timezone meeting",
        "acceptance_criteria": [
            "Given I connect my calendar, when a new event is created, "
            "then it appears in all participants' local time",
            "Sync completes within 2 seconds",
        ],
        "priority": "must",
        "epic": "Calendar Sync",
    }
]

_FAKE_ROADMAP = [
    {
        "phase": "MVP",
        "title": "Core Scheduling",
        "objective": "Enable basic cross-timezone scheduling.",
        "epics": ["Calendar Sync"],
        "user_story_ids": ["US-001"],
        "target_weeks": 8,
    }
]


class FakeProductPlannerLLMRouter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.should_fail = False
        # Cycle through staged responses
        self._responses = [
            json.dumps(_FAKE_PRD),
            json.dumps(_FAKE_REQUIREMENTS),
            json.dumps(_FAKE_USER_STORIES),
            json.dumps(_FAKE_ROADMAP),
        ]
        self._call_count = 0

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        self.calls.append((task_class, prompt))
        if self.should_fail:
            raise RuntimeError("FakeLLM forced failure")
        idx = self._call_count % len(self._responses)
        self._call_count += 1
        return self._responses[idx]


# ---------------------------------------------------------------------------
# Fake tool registry (NoToolRegistry is already in registry.py; this is for tests)
# ---------------------------------------------------------------------------


class FakeNoToolRegistry(ToolRegistryProtocol):
    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("ProductPlannerAgent does not use tools")


# ---------------------------------------------------------------------------
# Fake UDAL with cache + object store
# ---------------------------------------------------------------------------


def make_fake_udal(cache_data: dict | None = None) -> MagicMock:
    udal = MagicMock()

    # Cache
    cache = MagicMock()
    _store: dict[str, dict] = {}
    if cache_data:
        _store.update(cache_data)

    async def get_session(key: str) -> dict | None:
        return _store.get(key)

    async def set_session(key: str, data: dict, ttl: int = 86400) -> None:
        _store[key] = data

    cache.get_session = AsyncMock(side_effect=get_session)
    cache.set_session = AsyncMock(side_effect=set_session)
    udal.cache = cache

    # Object store
    obj = MagicMock()
    obj.upload = AsyncMock(return_value="https://storage.supabase.io/prds/run-001/prd.md")
    udal.object = MagicMock(return_value=obj)

    return udal


# ---------------------------------------------------------------------------
# Sample StrategyOutput
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_strategy() -> StrategyOutput:
    return StrategyOutput(
        run_id="run-001",
        organization_id="org-001",
        idea_normalised="AI-powered scheduling tool for remote teams",
        domain="B2B SaaS",
        tam_sam_som={"tam_usd_bn": 5.0, "sam_usd_bn": 0.5, "som_usd_bn": 0.05},
        competitors=[
            Competitor(name="Calendly", url="https://calendly.com", key_features=["scheduling"])
        ],
        icps=[
            BuyerPersona(
                name="Alex Chen",
                role="Engineering Manager",
                company_size="50-200",
                pain_points=["timezone confusion", "back-and-forth emails"],
                goals=["reduce scheduling overhead", "improve team availability"],
            )
        ],
        lean_canvas=LeanCanvas(
            problem=["Remote teams waste hours on scheduling"],
            customer_segments=["Engineering managers at distributed startups"],
            unique_value_proposition="Zero-effort cross-timezone scheduling",
            solution=["Smart calendar integration", "Timezone auto-detection"],
            channels=["LinkedIn", "Product Hunt"],
            revenue_streams=["Monthly SaaS subscription"],
            cost_structure=["Cloud hosting", "LLM API costs"],
            key_metrics=["Active users", "Meetings scheduled per week"],
            unfair_advantage="Proprietary scheduling algorithm",
            early_adopters="Distributed startup engineering teams",
        ),
        viability_score=78,
        viability_band="high",
        bias_flags=[],
        pivots=[],
        sources=["https://market.report/saas-scheduling"],
        report_markdown="# Strategy Report\n...",
        total_llm_tokens_used=4000,
    )


@pytest.fixture
def planner_input(sample_strategy: StrategyOutput) -> ProductPlannerInput:
    return ProductPlannerInput(
        run_id="run-001",
        organization_id="org-001",
        strategy=sample_strategy,
    )


@pytest.fixture
def fake_llm() -> FakeProductPlannerLLMRouter:
    return FakeProductPlannerLLMRouter()


@pytest.fixture
def fake_tools() -> FakeNoToolRegistry:
    return FakeNoToolRegistry()


@pytest.fixture
def fake_udal() -> MagicMock:
    return make_fake_udal()


@pytest.fixture
def sample_prd() -> PRD:
    return PRD(**_FAKE_PRD)


@pytest.fixture
def sample_requirements() -> list[Requirement]:
    return [Requirement(**r) for r in _FAKE_REQUIREMENTS]


@pytest.fixture
def sample_stories() -> list[UserStory]:
    return [UserStory(**s) for s in _FAKE_USER_STORIES]


@pytest.fixture
def sample_roadmap() -> list[Milestone]:
    return [Milestone(**m) for m in _FAKE_ROADMAP]


@pytest.fixture
def sample_output(
    sample_prd: PRD,
    sample_requirements: list[Requirement],
    sample_stories: list[UserStory],
    sample_roadmap: list[Milestone],
) -> ProductPlannerOutput:
    return ProductPlannerOutput(
        run_id="run-001",
        organization_id="org-001",
        domain="B2B SaaS",
        prd=sample_prd,
        requirements=sample_requirements,
        user_stories=sample_stories,
        roadmap=sample_roadmap,
        prd_markdown="# TeamSync\n...",
        coverage_score=0.85,
        confidence="high",
    )
