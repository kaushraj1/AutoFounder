"""Conditional edge routers for the Architect Agent StateGraph (AF-040).

Each function is passed the current state and returns the name of the
next node to route to. Used by LangGraph's add_conditional_edges().
"""

from __future__ import annotations

from app.agents.architect.state import ArchitectState


def route_after_design_join(state: ArchitectState) -> str:
    """After the join barrier: continue normally or abort on fatal errors."""
    if not state.get("design_complete", False):
        return "error_end"
    return "auth_strategy"


def route_after_featurelist(state: ArchitectState) -> str:
    """After FeatureList: fatal error if features list is empty."""
    feature_list = state.get("feature_list") or {}
    if not feature_list.get("features"):
        return "error_end"
    return "hitl_gate"


def route_after_hitl(state: ArchitectState) -> str:
    """After Founder Approval gate: approved → end, rejected → re-plan."""
    status = state.get("approval_status", "pending")
    if status == "approved":
        return "end"
    if status == "rejected":
        return "select_stack"  # loop back to redesign
    # Still pending — should not happen in a synchronous flow
    return "error_end"
