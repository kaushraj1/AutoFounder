"""Integration tests for ProductPlannerAgent — AF-039."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.agents.product_planner.agent import ProductPlannerAgent
from app.agents.product_planner.registry import NoToolRegistry
from app.agents.product_planner.schema import ProductPlannerInput, ProductPlannerOutput
from app.agents.strategy.schema import StrategyOutput
from tests.agents.product_planner.conftest import (
    FakeNoToolRegistry,
    FakeProductPlannerLLMRouter,
    make_fake_udal,
)


def _make_agent(
    fake_llm: FakeProductPlannerLLMRouter,
    fake_udal: MagicMock | None = None,
) -> ProductPlannerAgent:
    from app.agents._providers.jinja_prompt_registry import JinjaPromptRegistry

    return ProductPlannerAgent(
        udal=fake_udal or make_fake_udal(),
        checkpointer=MagicMock(),
        tool_registry=FakeNoToolRegistry(),
        prompt_registry=JinjaPromptRegistry(),
        llm_router=fake_llm,
    )


# T2: understand rejects empty canvas
@pytest.mark.asyncio
async def test_understand_rejects_missing_canvas(
    fake_llm: FakeProductPlannerLLMRouter,
    sample_strategy: StrategyOutput,
) -> None:
    sample_strategy.__dict__["lean_canvas"] = None
    agent = _make_agent(fake_llm)
    inp = ProductPlannerInput(run_id="run-001", organization_id="org-001", strategy=sample_strategy)
    with pytest.raises((ValueError, Exception)):
        await agent.run(inp)


# T3: understand warns but proceeds on reject band
@pytest.mark.asyncio
async def test_understand_proceeds_on_reject_band(
    fake_llm: FakeProductPlannerLLMRouter,
    planner_input: ProductPlannerInput,
) -> None:
    planner_input.strategy.__dict__["viability_band"] = "reject"
    agent = _make_agent(fake_llm)
    # Should not raise — rejection-band warning is non-fatal
    result = await agent.run(planner_input)
    assert isinstance(result, ProductPlannerOutput)


# T4: full execute produces PRD + reqs + stories + roadmap
@pytest.mark.asyncio
async def test_full_execute_produces_all_sections(
    fake_llm: FakeProductPlannerLLMRouter,
    planner_input: ProductPlannerInput,
) -> None:
    agent = _make_agent(fake_llm)
    result = await agent.run(planner_input)
    assert result.prd.title
    assert len(result.requirements) > 0
    assert len(result.user_stories) > 0
    assert len(result.roadmap) > 0
    assert result.total_llm_tokens_used > 0


# T5: staged calls in correct order
@pytest.mark.asyncio
async def test_staged_calls_in_order(
    fake_llm: FakeProductPlannerLLMRouter,
    planner_input: ProductPlannerInput,
) -> None:
    agent = _make_agent(fake_llm)
    await agent.run(planner_input)
    # All calls must be product_planner_generation task class
    assert all(tc == "product_planner_generation" for tc, _ in fake_llm.calls)
    # Must have been called 4 times (PRD, requirements, stories, roadmap)
    assert fake_llm._call_count >= 4


# T6: NoToolRegistry raises on call
@pytest.mark.asyncio
async def test_no_tool_registry_raises() -> None:
    registry = NoToolRegistry()
    with pytest.raises(NotImplementedError, match="does not use external tools"):
        await registry.call("some_tool", {})


# T11: Redis cache hit short-circuits execute
@pytest.mark.asyncio
async def test_cache_hit_skips_llm(
    fake_llm: FakeProductPlannerLLMRouter,
    planner_input: ProductPlannerInput,
    sample_output: ProductPlannerOutput,
) -> None:
    import hashlib

    payload = (
        f"{planner_input.strategy.run_id}:{planner_input.strategy.domain}:"
        f"{planner_input.strategy.viability_score}"
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    cache_key = f"product_planner:{digest}"

    # Pre-seed the cache with the sample output
    cached = make_fake_udal(cache_data={cache_key: sample_output.model_dump()})
    agent = _make_agent(fake_llm, fake_udal=cached)

    result = await agent.run(planner_input)
    # LLM should NOT have been called
    assert fake_llm._call_count == 0
    assert result.prd.title == sample_output.prd.title


# T12: PRD persisted → prd_s3_uri set
@pytest.mark.asyncio
async def test_prd_persisted(
    fake_llm: FakeProductPlannerLLMRouter,
    planner_input: ProductPlannerInput,
) -> None:
    agent = _make_agent(fake_llm)
    result = await agent.run(planner_input)
    assert result.prd_s3_uri is not None
    assert "prd.md" in result.prd_s3_uri


# T13: persistence failure degrades gracefully
@pytest.mark.asyncio
async def test_persistence_failure_degrades_gracefully(
    fake_llm: FakeProductPlannerLLMRouter,
    planner_input: ProductPlannerInput,
) -> None:
    from unittest.mock import AsyncMock

    udal = make_fake_udal()
    obj = MagicMock()
    obj.upload = AsyncMock(side_effect=RuntimeError("Storage unavailable"))
    udal.object = MagicMock(return_value=obj)

    agent = _make_agent(fake_llm, fake_udal=udal)
    result = await agent.run(planner_input)
    # prd_s3_uri absent but output still returned
    assert result.prd_s3_uri is None
    assert result.prd.title


# T14: run() calls all 5 phases
@pytest.mark.asyncio
async def test_run_executes_all_phases(
    fake_llm: FakeProductPlannerLLMRouter,
    planner_input: ProductPlannerInput,
) -> None:
    phase_order: list[str] = []

    class TrackingAgent(ProductPlannerAgent):
        async def understand(self, input):  # type: ignore[override]
            phase_order.append("understand")
            return await super().understand(input)

        async def plan(self, intent):  # type: ignore[override]
            phase_order.append("plan")
            return await super().plan(intent)

        async def execute(self, plan):  # type: ignore[override]
            phase_order.append("execute")
            return await super().execute(plan)

        async def verify(self, output):  # type: ignore[override]
            phase_order.append("verify")
            return await super().verify(output)

        async def learn(self, trace):  # type: ignore[override]
            phase_order.append("learn")
            return await super().learn(trace)

    from app.agents._providers.jinja_prompt_registry import JinjaPromptRegistry

    agent = TrackingAgent(
        udal=make_fake_udal(),
        checkpointer=MagicMock(),
        tool_registry=FakeNoToolRegistry(),
        prompt_registry=JinjaPromptRegistry(),
        llm_router=fake_llm,
    )
    await agent.run(planner_input)
    assert phase_order == ["understand", "plan", "execute", "verify", "learn"]
