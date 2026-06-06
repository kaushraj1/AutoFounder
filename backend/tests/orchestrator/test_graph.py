"""Integration tests for the StateGraph — nodes, edges, and gate routing (AF-033).

Requires the `agents` dep group: ``uv sync --group agents``
"""

import pytest

langgraph = pytest.importorskip("langgraph", reason="agents dep group not installed")

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from app.orchestrator.graph import build_run_graph  # noqa: E402
from app.orchestrator.state import make_initial_state  # noqa: E402


@pytest.fixture
def graph():
    return build_run_graph(MemorySaver())


def _config(run_id: str) -> dict:
    return {"configurable": {"thread_id": run_id, "checkpoint_ns": ""}}


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------


def test_graph_builds(graph):
    assert graph is not None


def test_graph_has_required_nodes(graph):
    all_nodes = set(graph.get_graph().nodes.keys())
    required = {
        "validate_input",
        "run_pillar_1",
        "validation_gate",
        "pivot_rerun",
        "run_pillar_2",
        "architecture_gate",
        "run_pillar_3",
        "run_pillar_4",
        "run_pillar_5",
        "infra_spend_gate",
        "run_pillar_6",
        "launch_gate",
        "run_pillar_7",
    }
    missing = required - all_nodes
    assert not missing, f"Missing nodes: {missing}"


# ---------------------------------------------------------------------------
# Behavioral tests — full async (asyncio_mode=auto in pyproject.toml)
# ---------------------------------------------------------------------------


async def test_run_pauses_at_validation_gate(graph):
    run_id = "gt-pause-val"
    state = make_initial_state(run_id, "org-1", "ws-1", "B2B SaaS idea")
    await graph.ainvoke(state, _config(run_id))

    snapshot = await graph.aget_state(_config(run_id))
    assert snapshot is not None
    vals = snapshot.values
    assert vals["current_pillar"] == 1
    assert vals["strategy_output"] is not None
    assert vals["status"] == "running"
    assert "validation_gate" in snapshot.next


async def test_empty_idea_fails_before_pillar_1(graph):
    run_id = "gt-empty-idea"
    state = make_initial_state(run_id, "org-1", "ws-1", "   ")
    result = await graph.ainvoke(state, _config(run_id))

    assert result["status"] == "failed"
    assert result["error"] is not None
    assert result["current_pillar"] is None  # never reached pillar 1


async def test_resume_approved_reaches_pillar_2(graph):
    run_id = "gt-approve-val"
    await graph.ainvoke(
        make_initial_state(run_id, "org-1", "ws-1", "DevTool idea"),
        _config(run_id),
    )

    await graph.aupdate_state(
        _config(run_id), {"gate_decision": "approved", "active_gate_id": None}
    )
    await graph.ainvoke(None, _config(run_id))

    snapshot = await graph.aget_state(_config(run_id))
    vals = snapshot.values
    assert vals["current_pillar"] == 2
    assert vals["architecture_output"] is not None
    assert "architecture_gate" in snapshot.next


async def test_resume_timed_out_ends_run(graph):
    run_id = "gt-timeout"
    await graph.ainvoke(
        make_initial_state(run_id, "org-1", "ws-1", "Any idea"),
        _config(run_id),
    )

    await graph.aupdate_state(_config(run_id), {"gate_decision": "timed_out"})
    await graph.ainvoke(None, _config(run_id))

    snapshot = await graph.aget_state(_config(run_id))
    assert not snapshot.next  # graph ended


async def test_pivot_loops_back_to_pillar_1(graph):
    run_id = "gt-pivot"
    await graph.ainvoke(
        make_initial_state(run_id, "org-1", "ws-1", "weak idea"),
        _config(run_id),
    )

    await graph.aupdate_state(
        _config(run_id),
        {"gate_decision": "rejected", "idea_text": "stronger B2B DevTool"},
    )
    await graph.ainvoke(None, _config(run_id))

    snapshot = await graph.aget_state(_config(run_id))
    vals = snapshot.values
    # After pivot: pillar 1 re-ran, paused at validation_gate again
    assert vals["retry_count"] == 1
    assert vals["idea_text"] == "stronger B2B DevTool"
    assert vals["current_pillar"] == 1
    assert "validation_gate" in snapshot.next


async def test_full_approved_pipeline_completes(graph):
    """Drive all three required gates with 'approved' and reach completed status."""
    run_id = "gt-full"
    config = _config(run_id)

    # Initial run → pauses at validation_gate
    await graph.ainvoke(make_initial_state(run_id, "org-1", "ws-1", "Full pipeline"), config)

    # Gate 1: validation
    await graph.aupdate_state(config, {"gate_decision": "approved"})
    await graph.ainvoke(None, config)

    # Gate 2: architecture
    await graph.aupdate_state(config, {"gate_decision": "approved"})
    await graph.ainvoke(None, config)

    # Gate 3: launch (infra_spend_gate skipped because cost_usd_cents=0)
    await graph.aupdate_state(config, {"gate_decision": "approved"})
    result = await graph.ainvoke(None, config)

    assert result["status"] == "completed"
    assert result["llmops_output"] is not None
    assert result["current_pillar"] == 7


async def test_step_events_accumulate_across_nodes(graph):
    """step_events uses operator.add reducer — must grow across checkpoints."""
    run_id = "gt-events"
    config = _config(run_id)

    await graph.ainvoke(make_initial_state(run_id, "org-1", "ws-1", "Events test"), config)

    snapshot = await graph.aget_state(config)
    # validate_input + run_pillar_1 should have emitted events
    assert len(snapshot.values["step_events"]) >= 2
    nodes_seen = {ev["node"] for ev in snapshot.values["step_events"]}
    assert "validate_input" in nodes_seen
    assert "run_pillar_1" in nodes_seen
