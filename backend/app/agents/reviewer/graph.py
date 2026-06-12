"""LangGraph StateGraph factory for the Reviewer agent (plan §3.3).

13 nodes + a central error sink. The five gates fan out from ``spin_sandbox`` and
converge at ``test_join``; the self-heal loop (``triage → auto_heal →
spin_sandbox``) is a first-class graph cycle bounded by ``MAX_HEAL_CYCLES``.
"""

from __future__ import annotations

from functools import partial
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.reviewer.nodes import (
    auto_heal,
    emit_report,
    error_handler,
    ingest_code,
    llm_judge,
    run_e2e_tests,
    run_linters,
    run_security_scan,
    run_sonarqube,
    run_unit_tests,
    spin_sandbox,
    teardown_sandbox,
    test_join,
    triage_failures,
)
from app.agents.reviewer.routers import (
    PARALLEL_GATES,
    route_after_ingest,
    route_after_join,
    route_after_judge,
    route_after_sandbox,
    route_after_triage,
    route_terminal,
)
from app.agents.reviewer.schema import ReviewerState


def build_reviewer_graph(agent: Any, checkpointer: Any) -> Any:
    """Build and compile the Reviewer stateful graph."""
    graph = StateGraph(ReviewerState)

    # -- Node registration (agent context injected via partial) -------------
    graph.add_node("ingest_code", partial(ingest_code, agent=agent))
    graph.add_node("spin_sandbox", partial(spin_sandbox, agent=agent))
    graph.add_node("run_linters", partial(run_linters, agent=agent))
    graph.add_node("run_unit_tests", partial(run_unit_tests, agent=agent))
    graph.add_node("run_e2e_tests", partial(run_e2e_tests, agent=agent))
    graph.add_node("run_security_scan", partial(run_security_scan, agent=agent))
    graph.add_node("run_sonarqube", partial(run_sonarqube, agent=agent))
    graph.add_node("test_join", test_join)
    graph.add_node("llm_judge", partial(llm_judge, agent=agent))
    graph.add_node("triage_failures", partial(triage_failures, agent=agent))
    graph.add_node("auto_heal", partial(auto_heal, agent=agent))
    graph.add_node("teardown_sandbox", partial(teardown_sandbox, agent=agent))
    graph.add_node("emit_report", partial(emit_report, agent=agent))
    graph.add_node("error_handler", partial(error_handler, agent=agent))

    # -- Entry --------------------------------------------------------------
    graph.set_entry_point("ingest_code")
    graph.add_conditional_edges(
        "ingest_code",
        route_after_ingest,
        {"spin_sandbox": "spin_sandbox", "error_handler": "error_handler"},
    )

    # -- Fan-out to the five parallel gates ---------------------------------
    graph.add_conditional_edges("spin_sandbox", route_after_sandbox)
    for gate in PARALLEL_GATES:
        graph.add_edge(gate, "test_join")

    # -- Barrier → judge → triage ------------------------------------------
    graph.add_conditional_edges(
        "test_join",
        route_after_join,
        {"llm_judge": "llm_judge", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "llm_judge",
        route_after_judge,
        {"triage_failures": "triage_failures", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "triage_failures",
        route_after_triage,
        {
            "teardown_sandbox": "teardown_sandbox",
            "auto_heal": "auto_heal",
            "error_handler": "error_handler",
        },
    )

    # -- Self-heal loop -----------------------------------------------------
    graph.add_edge("auto_heal", "spin_sandbox")

    # -- Approved path → report → END --------------------------------------
    graph.add_edge("teardown_sandbox", "emit_report")
    graph.add_conditional_edges(
        "emit_report",
        route_terminal,
        {"end": END, "error_handler": "error_handler"},
    )

    # -- Error sink exits ---------------------------------------------------
    graph.add_edge("error_handler", END)

    return graph.compile(checkpointer=checkpointer)
