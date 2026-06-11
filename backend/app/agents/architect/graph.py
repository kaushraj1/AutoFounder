"""LangGraph StateGraph for the Architect Agent (AF-040).

Graph topology (9 nodes):

  extract_requirements
        |
  [parallel fan-out via Send API]
  design_erd  ||  design_api_contract  ||  select_stack
        |
  design_join  (barrier)
        |
  auth_strategy
        |
  scaling_plan
        |
  cost_forecast
        |
  compose_featurelist
        |
  [HITL gate — approval_status checked by router]
    approved → END
    rejected → select_stack (re-design loop)
    fatal    → error_end

Standalone usage (no platform needed):
    from app.agents.architect.graph import build_architect_graph
    import json

    graph = build_architect_graph()
    prd = json.load(open("fixtures/saas_prd.json"))
    result = graph.invoke({
        "run_id": "test-001",
        "organization_id": "org-test",
        "idea_normalised": prd["idea_normalised"],
        "viability_band": prd["viability_band"],
        "lean_canvas": prd["lean_canvas"],
        "prd": prd["prd"],
        "approval_status": "approved",   # auto-approve for testing
        "errors": [],
        "llm_tokens_used": 0,
    })
    print(result["feature_list"])
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.architect.nodes.auth_strategy import auth_strategy
from app.agents.architect.nodes.compose_featurelist import compose_featurelist
from app.agents.architect.nodes.cost_forecast import cost_forecast
from app.agents.architect.nodes.design_api_contract import design_api_contract
from app.agents.architect.nodes.design_erd import design_erd
from app.agents.architect.nodes.design_join import design_join
from app.agents.architect.nodes.extract_requirements import extract_requirements
from app.agents.architect.nodes.scaling_plan import scaling_plan
from app.agents.architect.nodes.select_stack import select_stack
from app.agents.architect.routers import (
    route_after_design_join,
    route_after_featurelist,
    route_after_hitl,
)
from app.agents.architect.state import ArchitectState

logger = logging.getLogger(__name__)


def _hitl_gate(state: ArchitectState) -> ArchitectState:
    """HITL stub node.

    In standalone / test mode: reads approval_status from state directly
    (caller sets "approved" to skip the gate).

    In production: the Orchestrator (AF-033) pauses the graph here,
    emits a gate.required event, and resumes when the Founder responds
    via the Architecture Studio (AF-056).
    """
    status = state.get("approval_status", "pending")
    comment = state.get("rejection_comment")
    logger.info("[architect] hitl_gate — status=%s", status)

    if status == "rejected" and comment:
        logger.info("[architect] hitl_gate — rejection comment: %s", comment)

    return {**state, "approval_status": status}


def _error_end(state: ArchitectState) -> ArchitectState:
    """Terminal error node — logs all accumulated errors and stops."""
    errors = state.get("errors", [])
    logger.error("[architect] error_end — %d error(s):", len(errors))
    for err in errors:
        logger.error("  • %s", err)
    return state


def build_architect_graph() -> CompiledStateGraph:
    """Build and compile the Architect Agent StateGraph.

    Returns a compiled LangGraph graph ready for .invoke() or .stream().
    """
    builder = StateGraph(ArchitectState)

    # ---- Add nodes ------------------------------------------------
    builder.add_node("extract_requirements", extract_requirements)
    builder.add_node("design_erd", design_erd)
    builder.add_node("design_api_contract", design_api_contract)
    builder.add_node("select_stack", select_stack)
    builder.add_node("design_join", design_join)
    builder.add_node("auth_strategy", auth_strategy)
    builder.add_node("scaling_plan", scaling_plan)
    builder.add_node("cost_forecast", cost_forecast)
    builder.add_node("compose_featurelist", compose_featurelist)
    builder.add_node("hitl_gate", _hitl_gate)
    builder.add_node("error_end", _error_end)

    # ---- Edges: START → extract_requirements ----------------------
    builder.add_edge(START, "extract_requirements")

    # ---- Fan-out: extract_requirements → 3 parallel design nodes --
    builder.add_edge("extract_requirements", "design_erd")
    builder.add_edge("extract_requirements", "design_api_contract")
    builder.add_edge("extract_requirements", "select_stack")

    # ---- All 3 converge at design_join ----------------------------
    builder.add_edge("design_erd", "design_join")
    builder.add_edge("design_api_contract", "design_join")
    builder.add_edge("select_stack", "design_join")

    # ---- design_join → auth_strategy (or error) -------------------
    builder.add_conditional_edges(
        "design_join",
        route_after_design_join,
        {"auth_strategy": "auth_strategy", "error_end": "error_end"},
    )

    # ---- Linear chain: auth → scaling → cost → featurelist --------
    builder.add_edge("auth_strategy", "scaling_plan")
    builder.add_edge("scaling_plan", "cost_forecast")
    builder.add_edge("cost_forecast", "compose_featurelist")

    # ---- featurelist → hitl (or fatal error) ----------------------
    builder.add_conditional_edges(
        "compose_featurelist",
        route_after_featurelist,
        {"hitl_gate": "hitl_gate", "error_end": "error_end"},
    )

    # ---- hitl → END | re-design loop | error_end ------------------
    builder.add_conditional_edges(
        "hitl_gate",
        route_after_hitl,
        {
            "end": END,
            "select_stack": "select_stack",
            "error_end": "error_end",
        },
    )

    # ---- Terminal nodes -------------------------------------------
    builder.add_edge("error_end", END)

    return builder.compile()
