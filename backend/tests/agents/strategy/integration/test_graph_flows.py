import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.agents.strategy.agent import StrategyAgent
from app.agents.strategy.schema import ViabilityBand


@pytest.mark.asyncio
async def test_strategy_agent_happy_path(fake_llm, fake_tools, local_prompts, mock_udal):
    """Test full happy path with strong viability output and no pivots."""
    checkpointer = MemorySaver()
    agent = StrategyAgent(
        udal=mock_udal,
        checkpointer=checkpointer,
        tool_registry=fake_tools,
        prompt_registry=local_prompts,
        llm_router=fake_llm,
    )

    fake_llm.viability_score_override = 85

    input_data = {
        "organization_id": "test_org",
        "idea_raw": "A revolutionary developer platform for deploying multi-tenant AI agents.",
    }

    output = await agent.run(input_data)

    assert output.fatal_error is None
    assert output.viability_score.total == 85
    assert output.viability_score.band == ViabilityBand.STRONG
    assert len(output.viability_score.pivot_suggestions) == 0
    assert output.lean_canvas is not None
    assert len(output.competitors) > 0
    assert len(output.personas) > 0
    assert output.report_markdown is not None


@pytest.mark.asyncio
async def test_strategy_agent_low_viability_pivots(fake_llm, fake_tools, local_prompts, mock_udal):
    """Test low viability flow where pivot suggestions are successfully generated."""
    checkpointer = MemorySaver()
    agent = StrategyAgent(
        udal=mock_udal,
        checkpointer=checkpointer,
        tool_registry=fake_tools,
        prompt_registry=local_prompts,
        llm_router=fake_llm,
    )

    fake_llm.viability_score_override = 40

    input_data = {
        "organization_id": "test_org",
        "idea_raw": "A crowded, basic Todo app with no unique value prop.",
    }

    output = await agent.run(input_data)

    assert output.fatal_error is None
    assert output.viability_score.total == 40
    assert output.viability_score.band == ViabilityBand.WEAK
    assert len(output.viability_score.pivot_suggestions) >= 2
    assert "vertical API integration" in output.viability_score.pivot_suggestions[0]
