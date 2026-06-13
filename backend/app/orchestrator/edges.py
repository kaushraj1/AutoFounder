"""Conditional edge routing functions for the orchestrator StateGraph (AF-033).

Each function receives the CURRENT RunState (after the preceding node ran)
and returns the name of the next node to execute, or "__end__" to terminate.
"""

from __future__ import annotations

from app.orchestrator.state import RunState

_MAX_PIVOT_RETRIES = 3

# Infra spend gate fires when accumulated cost exceeds this threshold.
INFRA_SPEND_THRESHOLD_CENTS = 5_000  # $50


def route_after_validate_input(state: RunState) -> str:
    """Skip the pipeline if input validation failed."""
    return "__end__" if state.get("status") == "failed" else "run_pillar_1"


def route_after_validation_gate(state: RunState) -> str:
    """Approve → Pillar 2.  Reject (under retry limit) → pivot.  Otherwise end."""
    decision = state.get("gate_decision")
    if decision == "approved":
        return "run_pillar_2"
    if decision == "rejected":
        if (state.get("retry_count") or 0) < _MAX_PIVOT_RETRIES:
            return "pivot_rerun"
    return "__end__"


def route_after_pivot_rerun(state: RunState) -> str:
    """Always loops back to Pillar 1 for a pivot re-run."""
    return "run_pillar_1"


def route_after_architecture_gate(state: RunState) -> str:
    """Approve → Pillar 3.  Reject / timed-out → end."""
    return "run_pillar_3" if state.get("gate_decision") == "approved" else "__end__"


def route_after_pillar_5(state: RunState) -> str:
    """Fire infra-spend gate only when projected monthly cost exceeds threshold.

    Reads `deployment_output.monthly_cost_usd` (populated by run_pillar_5 from
    the DevOps agent's cost estimator) and converts to cents. Falls back to the
    legacy `cost_usd_cents` field when no deployment_output is present (keeps
    older tests/fixtures working).
    """
    deployment_output = state.get("deployment_output") or {}
    monthly_cost_usd = deployment_output.get("monthly_cost_usd")
    if monthly_cost_usd is not None:
        cost_cents = int(round(float(monthly_cost_usd) * 100))
    else:
        cost_cents = int(state.get("cost_usd_cents") or 0)
    if cost_cents > INFRA_SPEND_THRESHOLD_CENTS:
        return "infra_spend_gate"
    return "run_pillar_6"


def route_after_infra_spend_gate(state: RunState) -> str:
    """Approve → Pillar 6.  Reject / timed-out → end."""
    return "run_pillar_6" if state.get("gate_decision") == "approved" else "__end__"


def route_after_launch_gate(state: RunState) -> str:
    """Approve → Pillar 7.  Reject / timed-out → end."""
    return "run_pillar_7" if state.get("gate_decision") == "approved" else "__end__"
