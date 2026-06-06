"""Shared fixtures for Research Agent tests."""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.base import ToolRegistryProtocol
from app.agents.research.schema import Citation, ResearchFinding, ResearchInput, ResearchOutput

# ---------------------------------------------------------------------------
# Fake LLM router
# ---------------------------------------------------------------------------


class FakeResearchLLMRouter:
    def __init__(self) -> None:
        self.called: list[tuple[str, str]] = []
        self.should_fail = False
        self.findings_override: list[dict[str, Any]] | None = None

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        self.called.append((task_class, prompt))
        if self.should_fail:
            raise RuntimeError("FakeLLM forced failure")
        findings = self.findings_override or [
            {"claim": "Market is growing at 15% CAGR", "citations": [0, 1]},
            {"claim": "Top competitors raised $50M+", "citations": [2]},
            {"claim": "User pain: complex onboarding", "citations": [0]},
        ]
        return json.dumps(findings)


# ---------------------------------------------------------------------------
# Fake tool registry
# ---------------------------------------------------------------------------


class FakeToolRegistry(ToolRegistryProtocol):
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.fail_sources: set[str] = set()

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((tool_name, args))
        if tool_name in self.fail_sources:
            raise RuntimeError(f"Fake failure for {tool_name}")
        return {
            "citations": [
                {
                    "source": tool_name,
                    "url": f"https://example.com/{tool_name}",
                    "title": f"Result from {tool_name}",
                    "snippet": f"Mock data for {tool_name} query={args.get('query', '')}",
                }
            ]
        }


# ---------------------------------------------------------------------------
# Fake UDAL with cache
# ---------------------------------------------------------------------------


def make_fake_udal(cache_data: dict | None = None) -> MagicMock:
    udal = MagicMock()
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
    return udal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_llm() -> FakeResearchLLMRouter:
    return FakeResearchLLMRouter()


@pytest.fixture
def fake_tools() -> FakeToolRegistry:
    return FakeToolRegistry()


@pytest.fixture
def fake_udal() -> MagicMock:
    return make_fake_udal()


@pytest.fixture
def research_input() -> ResearchInput:
    return ResearchInput(
        run_id="run-001",
        organization_id="org-001",
        idea_normalised="AI-powered scheduling tool for remote teams",
        domain="B2B SaaS",
        sources=["tavily", "serpapi", "crunchbase", "g2", "similarweb"],
    )


@pytest.fixture
def sample_citations() -> list[Citation]:
    return [
        Citation(source="tavily", url="https://a.com", title="Market Report", snippet="15% CAGR"),
        Citation(source="serpapi", url="https://b.com",
                 title="Competitor Analysis", snippet="Top 5 competitors"),
        Citation(source="crunchbase", url="https://c.com",
                 title="Company X", snippet="$20M raised"),
    ]


@pytest.fixture
def sample_output(sample_citations: list[Citation]) -> ResearchOutput:
    return ResearchOutput(
        run_id="run-001",
        organization_id="org-001",
        domain="B2B SaaS",
        findings=[
            ResearchFinding(claim="Market growing 15% CAGR", citations=[0]),
            ResearchFinding(claim="Competitors well-funded", citations=[1, 2]),
            ResearchFinding(claim="No cited claim", citations=[]),
        ],
        sources=sample_citations,
        groundedness_score=0.67,
        confidence="low",
    )
