"""RunState — shared LangGraph state for all orchestrator nodes (AF-033)."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

RunStatus = Literal["queued", "running", "paused", "completed", "failed", "cancelled"]
GateDecision = Literal["approved", "rejected", "timed_out"]


class RunState(TypedDict):
    # Identity
    run_id: str
    organization_id: str
    workspace_id: str

    # Input
    idea_text: str
    idea_meta: dict[str, Any]

    # Execution
    status: RunStatus
    current_pillar: int | None
    current_node: str | None
    retry_count: int

    # Pillar outputs — None until that pillar executes
    strategy_output: dict[str, Any] | None
    architecture_output: dict[str, Any] | None
    code_output: dict[str, Any] | None
    review_output: dict[str, Any] | None
    deployment_output: dict[str, Any] | None
    marketing_output: dict[str, Any] | None
    llmops_output: dict[str, Any] | None

    # HITL gates
    active_gate_id: str | None
    gate_decision: GateDecision | None

    # Append-only execution log (operator.add reducer)
    step_events: Annotated[list[dict[str, Any]], operator.add]

    # Error
    error: str | None

    # Cost / token tracking
    total_tokens_used: int
    cost_usd_cents: int


def make_initial_state(
    run_id: str,
    organization_id: str,
    workspace_id: str,
    idea_text: str,
    idea_meta: dict[str, Any] | None = None,
) -> RunState:
    """Build a fully-populated RunState for a brand-new run."""
    return {
        "run_id": run_id,
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "idea_text": idea_text,
        "idea_meta": idea_meta or {},
        "status": "queued",
        "current_pillar": None,
        "current_node": None,
        "retry_count": 0,
        "strategy_output": None,
        "architecture_output": None,
        "code_output": None,
        "review_output": None,
        "deployment_output": None,
        "marketing_output": None,
        "llmops_output": None,
        "active_gate_id": None,
        "gate_decision": None,
        "step_events": [],
        "error": None,
        "total_tokens_used": 0,
        "cost_usd_cents": 0,
    }
