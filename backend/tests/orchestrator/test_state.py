"""Unit tests for RunState and make_initial_state (AF-033)."""

from app.orchestrator.state import make_initial_state


def test_make_initial_state_required_fields():
    state = make_initial_state("run-1", "org-1", "ws-1", "B2B SaaS idea")
    assert state["run_id"] == "run-1"
    assert state["organization_id"] == "org-1"
    assert state["workspace_id"] == "ws-1"
    assert state["idea_text"] == "B2B SaaS idea"


def test_make_initial_state_defaults():
    state = make_initial_state("r", "o", "w", "idea")
    assert state["status"] == "queued"
    assert state["current_pillar"] is None
    assert state["current_node"] is None
    assert state["retry_count"] == 0
    assert state["step_events"] == []
    assert state["error"] is None
    assert state["total_tokens_used"] == 0
    assert state["cost_usd_cents"] == 0
    assert state["gate_decision"] is None
    assert state["active_gate_id"] is None
    assert state["idea_meta"] == {}


def test_all_pillar_outputs_none():
    state = make_initial_state("r", "o", "w", "idea")
    for key in (
        "strategy_output",
        "architecture_output",
        "code_output",
        "review_output",
        "deployment_output",
        "marketing_output",
        "llmops_output",
    ):
        assert state[key] is None, f"{key} should start as None"


def test_idea_meta_custom():
    meta = {"locale": "en-IN", "source": "pdf"}
    state = make_initial_state("r", "o", "w", "idea", idea_meta=meta)
    assert state["idea_meta"] == meta


def test_idea_meta_not_shared():
    """Default {} must not be the same object across calls (mutable default trap)."""
    s1 = make_initial_state("r1", "o", "w", "idea1")
    s2 = make_initial_state("r2", "o", "w", "idea2")
    s1["idea_meta"]["x"] = 1
    assert "x" not in s2["idea_meta"]
