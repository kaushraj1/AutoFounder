from functools import partial
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.strategy.nodes import (
    analyze_trends,
    audit_bias,
    discover_competitors,
    error_handler,
    generate_personas,
    mine_keywords,
    normalize_idea,
    parallel_join,
    render_report,
    score_viability,
    size_market,
    synthesize_canvas,
)
from app.agents.strategy.routers import (
    route_after_audit,
    route_after_join,
    route_after_normalize,
    route_terminal,
)
from app.agents.strategy.schema import StrategistState


def build_strategist_graph(agent: Any, checkpointer: Any) -> Any:
    """Build and compile the Strategist stateful graph."""
    graph = StateGraph(StrategistState)

    # -- Node registration with agent context injection --------------------
    graph.add_node("normalize_idea", partial(normalize_idea, agent=agent))
    graph.add_node("size_market", partial(size_market, agent=agent))
    graph.add_node("discover_competitors", partial(discover_competitors, agent=agent))
    graph.add_node("mine_keywords", partial(mine_keywords, agent=agent))
    graph.add_node("generate_personas", partial(generate_personas, agent=agent))
    graph.add_node("analyze_trends", partial(analyze_trends, agent=agent))
    graph.add_node("parallel_join", parallel_join)
    graph.add_node("audit_bias", partial(audit_bias, agent=agent))
    graph.add_node("synthesize_canvas", partial(synthesize_canvas, agent=agent))
    graph.add_node("score_viability", partial(score_viability, agent=agent))
    graph.add_node("render_report", partial(render_report, agent=agent))
    graph.add_node("error_handler", error_handler)

    # -- Entry point --------------------------------------------------------
    graph.set_entry_point("normalize_idea")

    # -- Fan-out to parallel research branches (conditional) ----------------
    graph.add_conditional_edges(
        "normalize_idea",
        route_after_normalize,
    )

    # -- All parallel branches converge at the barrier ----------------------
    for node in (
        "size_market",
        "discover_competitors",
        "mine_keywords",
        "generate_personas",
        "analyze_trends",
    ):
        graph.add_edge(node, "parallel_join")

    # -- Post-join routing --------------------------------------------------
    graph.add_conditional_edges(
        "parallel_join",
        route_after_join,
        {
            "audit_bias": "audit_bias",
            "error_handler": "error_handler",
        },
    )

    # -- Sequential synthesis chain -----------------------------------------
    graph.add_conditional_edges(
        "audit_bias",
        route_after_audit,
        {
            "synthesize_canvas": "synthesize_canvas",
            "error_handler": "error_handler",
        },
    )

    graph.add_edge("synthesize_canvas", "score_viability")
    graph.add_edge("score_viability", "render_report")

    # -- Terminal routing ---------------------------------------------------
    graph.add_conditional_edges(
        "render_report",
        route_terminal,
        {
            "end": END,
            "error_handler": "error_handler",
        },
    )

    # -- Error handler exits ------------------------------------------------
    graph.add_edge("error_handler", END)

    return graph.compile(checkpointer=checkpointer)
