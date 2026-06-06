"""StateGraph factory — wires all pillar nodes, edges, and HITL gates (AF-033).

Call ``build_run_graph()`` once at startup and reuse the compiled graph.
Pass a ``BaseCheckpointSaver`` for persistence; omit it to get a MemorySaver
(suitable for tests and local development without a database).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver

# HITL gate nodes that trigger interrupt_before in the compiled graph.
# The graph pauses BEFORE each of these nodes until OrchestratorEngine.resume()
# injects a gate_decision and re-invokes.
_GATE_NODES: list[str] = [
    "validation_gate",
    "architecture_gate",
    "infra_spend_gate",
    "launch_gate",
]


def build_run_graph(checkpointer: BaseCheckpointSaver | None = None) -> Any:
    """Build and compile the 7-pillar StateGraph.

    Returns a ``CompiledStateGraph`` ready for ``ainvoke`` / ``aupdate_state``
    / ``aget_state``.
    """
    from langgraph.graph import END, START, StateGraph

    from app.orchestrator import edges, nodes
    from app.orchestrator.state import RunState

    if checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver

        checkpointer = MemorySaver()

    g: StateGraph = StateGraph(RunState)

    # ------------------------------------------------------------------ nodes
    g.add_node("validate_input", nodes.validate_input)
    g.add_node("run_pillar_1", nodes.run_pillar_1)
    g.add_node("validation_gate", nodes.validation_gate)
    g.add_node("pivot_rerun", nodes.pivot_rerun)
    g.add_node("run_pillar_2", nodes.run_pillar_2)
    g.add_node("architecture_gate", nodes.architecture_gate)
    g.add_node("run_pillar_3", nodes.run_pillar_3)
    g.add_node("run_pillar_4", nodes.run_pillar_4)
    g.add_node("run_pillar_5", nodes.run_pillar_5)
    g.add_node("infra_spend_gate", nodes.infra_spend_gate)
    g.add_node("run_pillar_6", nodes.run_pillar_6)
    g.add_node("launch_gate", nodes.launch_gate)
    g.add_node("run_pillar_7", nodes.run_pillar_7)

    # ------------------------------------------------------------------ edges
    g.add_edge(START, "validate_input")

    g.add_conditional_edges(
        "validate_input",
        edges.route_after_validate_input,
        {"run_pillar_1": "run_pillar_1", "__end__": END},
    )

    g.add_edge("run_pillar_1", "validation_gate")

    g.add_conditional_edges(
        "validation_gate",
        edges.route_after_validation_gate,
        {
            "run_pillar_2": "run_pillar_2",
            "pivot_rerun": "pivot_rerun",
            "__end__": END,
        },
    )

    g.add_conditional_edges(
        "pivot_rerun",
        edges.route_after_pivot_rerun,
        {"run_pillar_1": "run_pillar_1"},
    )

    g.add_edge("run_pillar_2", "architecture_gate")

    g.add_conditional_edges(
        "architecture_gate",
        edges.route_after_architecture_gate,
        {"run_pillar_3": "run_pillar_3", "__end__": END},
    )

    g.add_edge("run_pillar_3", "run_pillar_4")
    g.add_edge("run_pillar_4", "run_pillar_5")

    g.add_conditional_edges(
        "run_pillar_5",
        edges.route_after_pillar_5,
        {"infra_spend_gate": "infra_spend_gate", "run_pillar_6": "run_pillar_6"},
    )

    g.add_conditional_edges(
        "infra_spend_gate",
        edges.route_after_infra_spend_gate,
        {"run_pillar_6": "run_pillar_6", "__end__": END},
    )

    g.add_edge("run_pillar_6", "launch_gate")

    g.add_conditional_edges(
        "launch_gate",
        edges.route_after_launch_gate,
        {"run_pillar_7": "run_pillar_7", "__end__": END},
    )

    g.add_edge("run_pillar_7", END)

    # Compile with HITL interrupt points
    return g.compile(
        checkpointer=checkpointer,
        interrupt_before=_GATE_NODES,
    )
