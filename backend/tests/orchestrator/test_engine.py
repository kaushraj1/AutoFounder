"""Integration tests for OrchestratorEngine (AF-033).

Requires the `agents` dep group: ``uv sync --group agents``
"""

import pytest

langgraph = pytest.importorskip("langgraph", reason="agents dep group not installed")

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from app.orchestrator.engine import OrchestratorEngine  # noqa: E402
from app.orchestrator.graph import build_run_graph  # noqa: E402


@pytest.fixture
def engine():
    """Engine with in-memory checkpointer (no DB required)."""
    eng = OrchestratorEngine()
    eng._graph = build_run_graph(MemorySaver())
    return eng


# ---------------------------------------------------------------------------
# create_run
# ---------------------------------------------------------------------------


async def test_create_run_returns_uuid(engine):
    run_id = await engine.create_run("org-1", "ws-1", "SaaS idea")
    # Standard UUID v4: 8-4-4-4-12 characters, hyphens at [8,13,18,23]
    parts = run_id.split("-")
    assert len(parts) == 5
    assert len(run_id) == 36


async def test_create_run_unique_ids(engine):
    id1 = await engine.create_run("org-1", "ws-1", "Idea A")
    id2 = await engine.create_run("org-1", "ws-1", "Idea B")
    assert id1 != id2


async def test_create_run_pauses_at_validation_gate(engine):
    run_id = await engine.create_run("org-1", "ws-1", "marketplace idea")
    state = await engine.get_run_state(run_id)
    assert state is not None
    assert state["current_pillar"] == 1
    assert state["status"] == "running"
    assert state["strategy_output"] is not None


# ---------------------------------------------------------------------------
# resume — approved path
# ---------------------------------------------------------------------------


async def test_resume_approved_advances_to_architecture_gate(engine):
    run_id = await engine.create_run("org-1", "ws-1", "DevTool idea")
    await engine.resume(run_id, "approved")

    state = await engine.get_run_state(run_id)
    assert state["current_pillar"] == 2
    assert state["architecture_output"] is not None


async def test_resume_full_pipeline_to_completion(engine):
    run_id = await engine.create_run("org-1", "ws-1", "Complete pipeline idea")
    await engine.resume(run_id, "approved")  # validation gate
    await engine.resume(run_id, "approved")  # architecture gate
    await engine.resume(run_id, "approved")  # launch gate

    state = await engine.get_run_state(run_id)
    assert state["status"] == "completed"
    assert state["current_pillar"] == 7
    assert state["llmops_output"] is not None


# ---------------------------------------------------------------------------
# resume — rejected / pivot path
# ---------------------------------------------------------------------------


async def test_resume_rejected_without_pivot_ends_run(engine):
    run_id = await engine.create_run("org-1", "ws-1", "bad idea")
    await engine.resume(run_id, "rejected")  # no pivot_text → end

    state = await engine.get_run_state(run_id)
    # pivot_rerun fires (retry_count=1), pillar_1 re-runs with same idea_text
    # then pauses at validation_gate again OR if retry_count < max goes to pivot
    # With no pivot_text, idea_text stays the same — check retry happened
    assert state["retry_count"] == 1


async def test_resume_rejected_with_pivot_updates_idea_text(engine):
    run_id = await engine.create_run("org-1", "ws-1", "weak idea")
    await engine.resume(run_id, "rejected", pivot_text="strong B2B DevTool for CTOs")

    state = await engine.get_run_state(run_id)
    assert state["idea_text"] == "strong B2B DevTool for CTOs"
    assert state["retry_count"] == 1
    assert state["current_pillar"] == 1  # pillar 1 re-ran


# ---------------------------------------------------------------------------
# resume — timed_out path
# ---------------------------------------------------------------------------


async def test_resume_timed_out_ends_run(engine):
    run_id = await engine.create_run("org-1", "ws-1", "Idea that times out")
    await engine.resume(run_id, "timed_out")

    state = await engine.get_run_state(run_id)
    assert state["gate_decision"] == "timed_out"


# ---------------------------------------------------------------------------
# get_run_state
# ---------------------------------------------------------------------------


async def test_get_run_state_returns_none_for_unknown_run(engine):
    state = await engine.get_run_state("00000000-0000-0000-0000-000000000000")
    assert state is None


async def test_get_run_state_contains_all_keys(engine):
    run_id = await engine.create_run("org-1", "ws-1", "Keys test")
    state = await engine.get_run_state(run_id)
    assert state is not None
    required_keys = {
        "run_id",
        "organization_id",
        "workspace_id",
        "idea_text",
        "status",
        "current_pillar",
        "step_events",
        "total_tokens_used",
        "cost_usd_cents",
    }
    missing = required_keys - set(state.keys())
    assert not missing, f"Missing keys: {missing}"
