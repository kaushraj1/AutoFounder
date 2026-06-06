"""Failure-path tests for the Strategy Agent — exercises the BaseAgent contract
(typed errors, circuit breaker, SLA budget) and verify() gating."""

import asyncio

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.agents.base import (
    CircuitOpenError,
    LLMError,
    SLAExceededError,
    UnderstandError,
    VerifyError,
)
from app.agents.strategy.agent import StrategyAgent
from app.agents.strategy.schema import StrategistState


def _make_agent(fake_llm, fake_tools, local_prompts, mock_udal) -> StrategyAgent:
    return StrategyAgent(
        udal=mock_udal,
        checkpointer=MemorySaver(),
        tool_registry=fake_tools,
        prompt_registry=local_prompts,
        llm_router=fake_llm,
    )


@pytest.mark.asyncio
async def test_empty_idea_raises_understand_error(fake_llm, fake_tools, local_prompts, mock_udal):
    """An idea shorter than 10 chars must fail fast as UnderstandError, never fabricate a market."""
    agent = _make_agent(fake_llm, fake_tools, local_prompts, mock_udal)
    with pytest.raises(UnderstandError):
        await agent.run({"organization_id": "test_org", "idea_raw": "too short"})


@pytest.mark.asyncio
async def test_tool_failure_is_resilient(fake_llm, fake_tools, local_prompts, mock_udal):
    """All research tools failing must NOT fail the run — nodes swallow tool errors
    and proceed (lower groundedness), so the run still completes with a viability score."""
    fake_tools.should_fail = True
    agent = _make_agent(fake_llm, fake_tools, local_prompts, mock_udal)

    output = await agent.run(
        {"organization_id": "test_org", "idea_raw": "A platform for deploying AI agents at scale."}
    )

    assert output.fatal_error is None
    assert output.viability_score is not None
    assert output.report_markdown is not None


@pytest.mark.asyncio
async def test_llm_breaker_opens_after_threshold(fake_llm, fake_tools, local_prompts, mock_udal):
    """After failure_threshold (5) consecutive LLM failures the breaker OPENs and
    fast-fails subsequent calls with CircuitOpenError."""
    fake_llm.should_fail = True
    agent = _make_agent(fake_llm, fake_tools, local_prompts, mock_udal)

    # First 5 calls fail through to LLMError, tripping the breaker to OPEN.
    for _ in range(5):
        with pytest.raises(LLMError):
            await agent._call_llm(task_class="size_market", prompt="x")

    # 6th call is rejected fast by the OPEN breaker.
    with pytest.raises(CircuitOpenError):
        await agent._call_llm(task_class="size_market", prompt="x")


@pytest.mark.asyncio
async def test_sla_exceeded_raises(fake_llm, fake_tools, local_prompts, mock_udal):
    """Blowing the SLA budget surfaces as SLAExceededError (mapped from asyncio timeout)."""
    agent = _make_agent(fake_llm, fake_tools, local_prompts, mock_udal)
    agent.SLA_SECONDS = 0.05  # type: ignore[assignment]

    async def slow_execute(plan: dict) -> StrategistState:
        await asyncio.sleep(0.3)
        return plan["initial_state"]

    agent.execute = slow_execute  # type: ignore[assignment]

    with pytest.raises(SLAExceededError):
        await agent.run(
            {"organization_id": "test_org", "idea_raw": "A valid idea that is long enough."}
        )


@pytest.mark.asyncio
async def test_verify_gates_incomplete_output(fake_llm, fake_tools, local_prompts, mock_udal):
    """verify() must RAISE (not silently pass) when the run produced no canvas/score/report."""
    agent = _make_agent(fake_llm, fake_tools, local_prompts, mock_udal)
    incomplete = StrategistState(
        organization_id="test_org",
        idea_raw="A valid idea that is long enough to pass.",
    )
    with pytest.raises(VerifyError):
        await agent.verify(incomplete)
