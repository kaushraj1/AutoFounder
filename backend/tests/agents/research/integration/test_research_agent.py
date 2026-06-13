"""T8, T10–T13 — ResearchAgent integration: happy path, cache, retry, breaker."""

from __future__ import annotations

import pytest

from app.agents._providers import JinjaPromptRegistry
from app.agents.research.agent import ResearchAgent
from app.agents.research.schema import ResearchInput
from tests.agents.research.conftest import (
    FakeResearchLLMRouter,
    FakeToolRegistry,
    make_fake_udal,
)


def _make_agent(
    fake_llm: FakeResearchLLMRouter,
    fake_tools: FakeToolRegistry,
    udal=None,
    cache_data: dict | None = None,
) -> ResearchAgent:
    return ResearchAgent(
        udal=udal or make_fake_udal(cache_data),
        checkpointer=None,
        tool_registry=fake_tools,
        prompt_registry=JinjaPromptRegistry(),
        llm_router=fake_llm,
    )


# ---------------------------------------------------------------------------
# T8 — synthesis produces cited findings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_produces_cited_findings(
    fake_llm: FakeResearchLLMRouter,
    fake_tools: FakeToolRegistry,
    research_input: ResearchInput,
) -> None:
    agent = _make_agent(fake_llm, fake_tools)
    output = await agent.run(research_input)

    assert len(output.findings) >= 1
    assert output.sources
    cited = [f for f in output.findings if f.citations]
    assert cited, "Expected at least one finding with citations"


# ---------------------------------------------------------------------------
# T10 — low groundedness → retry synthesis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_low_groundedness_triggers_retry(
    fake_tools: FakeToolRegistry,
    research_input: ResearchInput,
) -> None:
    call_count = 0

    class LowGroundLLM:
        async def complete(self, *, task_class: str, prompt: str, **kw):
            nonlocal call_count
            call_count += 1
            # First call: no citations → low groundedness → triggers retry
            if call_count == 1:
                import json

                return json.dumps([{"claim": "Uncited claim", "citations": []}])
            # Second call: proper citations
            import json

            return json.dumps(
                [
                    {"claim": "Cited claim", "citations": [0]},
                    {"claim": "Another cited", "citations": [1]},
                ]
            )

    agent = _make_agent(LowGroundLLM(), fake_tools)
    output = await agent.run(research_input)

    assert call_count >= 2, "Expected at least one retry synthesis call"
    assert output.confidence in ("medium", "high", "low")


# ---------------------------------------------------------------------------
# T11 — Redis cache hit short-circuits tool calls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_hit_skips_tool_calls(
    fake_llm: FakeResearchLLMRouter,
    research_input: ResearchInput,
) -> None:
    # Pre-build cache key the same way agent would
    import hashlib

    srcs = ",".join(sorted(research_input.sources))
    payload = f"{research_input.domain}:{research_input.idea_normalised}:{srcs}"
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    cache_key = f"research:{digest}"

    from app.agents.research.schema import ResearchOutput

    cached_output = ResearchOutput(
        run_id="run-001",
        organization_id="org-001",
        domain="B2B SaaS",
        findings=[{"claim": "Cached finding", "citations": [0]}],
        sources=[{"source": "tavily", "snippet": "cached", "url": None, "title": None}],
        groundedness_score=0.8,
        confidence="high",
    ).model_dump()

    fresh_tools = FakeToolRegistry()
    agent = _make_agent(fake_llm, fresh_tools, cache_data={cache_key: cached_output})
    output = await agent.run(research_input)

    assert fresh_tools.calls == [], "Tools should NOT be called on cache hit"
    assert output.confidence == "high"


# ---------------------------------------------------------------------------
# T12 — circuit breaker opens after repeated tool failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_breaker_opens_after_repeated_tool_failure(
    fake_llm: FakeResearchLLMRouter,
    research_input: ResearchInput,
) -> None:

    call_count = 0

    class AlwaysFailTools:
        async def call(self, tool_name: str, args: dict) -> dict:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Tool always fails")

    agent = _make_agent(fake_llm, AlwaysFailTools())
    # Drive breaker open by exhausting failure_threshold (default 5)
    for _ in range(6):
        try:
            await agent._call_tool("tavily", {"query": "test"})
        except Exception:
            pass

    from app.agents.base import CircuitOpenError as COE

    with pytest.raises(COE):
        await agent._call_tool("tavily", {"query": "after open"})


# ---------------------------------------------------------------------------
# T13 — run() calls phases in order
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_calls_phases_in_order(
    fake_tools: FakeToolRegistry,
    research_input: ResearchInput,
) -> None:
    phases: list[str] = []

    class TracingLLM:
        async def complete(self, *, task_class: str, prompt: str, **kw):
            phases.append(f"llm:{task_class}")
            import json

            return json.dumps([{"claim": "traced", "citations": [0]}])

    agent = _make_agent(TracingLLM(), fake_tools)

    original_understand = agent.understand
    original_plan = agent.plan
    original_execute = agent.execute
    original_verify = agent.verify
    original_learn = agent.learn

    async def wrap_understand(i):
        phases.append("understand")
        return await original_understand(i)

    async def wrap_plan(i):
        phases.append("plan")
        return await original_plan(i)

    async def wrap_execute(p):
        phases.append("execute")
        return await original_execute(p)

    async def wrap_verify(o):
        phases.append("verify")
        return await original_verify(o)

    async def wrap_learn(t):
        phases.append("learn")
        return await original_learn(t)

    agent.understand = wrap_understand
    agent.plan = wrap_plan
    agent.execute = wrap_execute
    agent.verify = wrap_verify
    agent.learn = wrap_learn

    await agent.run(research_input)

    # learn always fires in finally — check all 5 lifecycle hooks present in order
    lifecycle = [p for p in phases if p in {"understand", "plan", "execute", "verify", "learn"}]
    assert lifecycle == ["understand", "plan", "execute", "verify", "learn"]
