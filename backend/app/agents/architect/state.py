"""LangGraph state for the Architect Agent (AF-040).

ArchitectState is the single shared dict that flows through every node
in the StateGraph. Each node reads what it needs and writes its output
back to the state — LangGraph merges changes automatically.

Design rules:
- All fields are Optional so nodes can run in any order / partial state.
- Upstream input fields (prd, lean_canvas, ...) are populated before
  the graph starts.
- Downstream output fields are populated as nodes complete.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any

from typing_extensions import TypedDict


class ArchitectState(TypedDict, total=False):
    # ------------------------------------------------------------------
    # Inputs (set before graph.invoke)
    # ------------------------------------------------------------------
    run_id: str
    organization_id: str
    idea_normalised: str
    viability_band: str
    lean_canvas: dict[str, Any]
    prd: str

    # ------------------------------------------------------------------
    # Node 1 — extract_requirements
    # ------------------------------------------------------------------
    requirements: list[dict[str, Any]]   # list[Requirement]
    use_cases: list[dict[str, Any]]

    # ------------------------------------------------------------------
    # Node 2a — design_erd  (parallel fan-out)
    # ------------------------------------------------------------------
    erd_mermaid: str
    erd_entities: list[str]
    erd_indexes: list[dict[str, Any]]
    erd_design_notes: str

    # ------------------------------------------------------------------
    # Node 2b — design_api_contract  (parallel fan-out)
    # ------------------------------------------------------------------
    openapi_3_1: dict[str, Any]
    openapi_valid: bool
    openapi_errors: list[str]

    # ------------------------------------------------------------------
    # Node 2c — select_stack  (parallel fan-out)
    # ------------------------------------------------------------------
    stack: dict[str, str]
    microservice_boundaries: list[str]
    stack_rationale: dict[str, str]
    stack_deviations: list[str]

    # ------------------------------------------------------------------
    # Node 3 — design_join (barrier — no new fields, just signals merge)
    # ------------------------------------------------------------------
    design_complete: bool

    # ------------------------------------------------------------------
    # Node 4 — auth_strategy
    # ------------------------------------------------------------------
    auth_strategy: dict[str, Any]

    # ------------------------------------------------------------------
    # Node 5 — scaling_plan
    # ------------------------------------------------------------------
    scaling_plan: dict[str, Any]

    # ------------------------------------------------------------------
    # Node 6 — cost_forecast
    # ------------------------------------------------------------------
    cost_estimate: dict[str, Any]
    pricing_source: str   # "live" | "static_fallback"

    # ------------------------------------------------------------------
    # Node 7 — compose_featurelist
    # ------------------------------------------------------------------
    feature_list: dict[str, Any]   # FeatureList shape

    # ------------------------------------------------------------------
    # HITL gate
    # ------------------------------------------------------------------
    approval_status: str   # "pending" | "approved" | "rejected"
    rejection_comment: str | None

    # ------------------------------------------------------------------
    # Errors / metadata
    # Annotated with reducers so parallel nodes can safely append/add
    # without causing InvalidUpdateError in LangGraph.
    # ------------------------------------------------------------------
    errors: Annotated[list[str], operator.add]
    llm_tokens_used: Annotated[int, operator.add]
