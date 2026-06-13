"""Orchestrator nodes — one stub per pillar + HITL gate nodes (AF-033).

Each node accepts the full RunState and returns a *partial* dict; LangGraph
merges it with the current state.  Pillar nodes are stubs until the actual
agent classes land (AF-036 – AF-045).
"""

from __future__ import annotations

import datetime
from typing import Any

from app.orchestrator.state import RunState


def _event(node: str, pillar: int | None, msg: str, **extra: Any) -> dict[str, Any]:
    return {
        "node": node,
        "pillar": pillar,
        "message": msg,
        "ts": datetime.datetime.now(datetime.UTC).isoformat(),
        **extra,
    }


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


async def validate_input(state: RunState) -> dict[str, Any]:
    """Sanitize idea text; transition status from queued → running."""
    idea = state["idea_text"].strip()
    if not idea:
        return {
            "status": "failed",
            "error": "idea_text is empty",
            "current_node": "validate_input",
            "step_events": [_event("validate_input", None, "Validation failed: empty idea")],
        }
    return {
        "idea_text": idea,
        "status": "running",
        "current_node": "validate_input",
        "error": None,
        "step_events": [_event("validate_input", None, "Input validated")],
    }


# ---------------------------------------------------------------------------
# Pillar 1 — Strategy & Ideation
# ---------------------------------------------------------------------------


async def run_pillar_1(state: RunState) -> dict[str, Any]:
    """Pillar 1: Strategy & Ideation. Wired to StrategyAgent (AF-037)."""
    from app.core.config import get_settings

    settings = get_settings()

    if not settings.gemini_api_key:
        return {
            "current_pillar": 1,
            "current_node": "run_pillar_1",
            "strategy_output": {
                "stub": True,
                "viability_band": "moderate",
                "viability_score": 65,
                "lean_canvas": {
                    "problem": ["Mock problem 1"],
                    "customer_segments": ["Mock segments 1"],
                    "unique_value_proposition": "Mock UVP",
                    "solution": ["Mock solution 1"],
                    "unfair_advantage": "Mock unfair advantage",
                    "early_adopters": "Mock early adopters",
                },
                "icps": [],
                "competitors": [],
                "pivots": [],
                "sources": [],
            },
            "step_events": [
                _event("run_pillar_1", 1, "Pillar 1 stub complete (no Gemini API Key)")
            ],
        }

    from app.agents._providers import GeminiRouter, JinjaPromptRegistry
    from app.agents.strategy import StrategyAgent
    from app.agents.strategy.schema import StrategyOutput
    from app.agents.strategy.tools import LocalToolRegistry
    from app.core.security import Principal
    from app.db.redis_pool import get_redis
    from app.db.session import SessionLocal
    from app.db.udal import UDAL
    from app.orchestrator.checkpointer import DualCheckpointer

    try:
        redis_client = get_redis()
    except RuntimeError:
        redis_client = None

    principal = Principal(organization_id=state["organization_id"], role="system")

    async with SessionLocal() as db_session:
        udal = UDAL(principal=principal, session=db_session, redis=redis_client)
        checkpointer = DualCheckpointer(session_factory=SessionLocal, redis=redis_client)
        tool_registry = LocalToolRegistry()
        prompt_registry = JinjaPromptRegistry()
        llm_router = GeminiRouter(
            api_key=settings.gemini_api_key, default_model=settings.strategy_model
        )

        agent = StrategyAgent(
            udal=udal,
            checkpointer=checkpointer,
            tool_registry=tool_registry,
            prompt_registry=prompt_registry,
            llm_router=llm_router,
        )

        agent_input = {
            "run_id": state["run_id"],
            "organization_id": state["organization_id"],
            "idea_raw": state["idea_text"],
        }

        try:
            output_state = await agent.run(agent_input)
            flat_output = StrategyOutput.from_state(output_state).model_dump()

            return {
                "current_pillar": 1,
                "current_node": "run_pillar_1",
                "strategy_output": flat_output,
                "step_events": [
                    _event("run_pillar_1", 1, "Pillar 1 StrategyAgent execution successful"),
                ],
            }
        except Exception as e:
            return {
                "current_pillar": 1,
                "current_node": "run_pillar_1",
                "status": "failed",
                "error": f"StrategyAgent run failed: {str(e)}",
                "step_events": [
                    _event("run_pillar_1", 1, f"StrategyAgent run failed: {str(e)}"),
                ],
            }


async def validation_gate(state: RunState) -> dict[str, Any]:
    """HITL gate — graph pauses *before* this node (interrupt_before).

    Runs only after OrchestratorEngine.resume() injects gate_decision via
    update_state and re-invokes.  Logs the decision; routing in edges.py.
    """
    decision = state.get("gate_decision") or "pending"
    return {
        "current_node": "validation_gate",
        "step_events": [_event("validation_gate", 1, f"Gate decision processed: {decision}")],
    }


async def pivot_rerun(state: RunState) -> dict[str, Any]:
    """Loop node: prepare for a Pillar 1 re-run with the pivot idea."""
    new_retry = (state.get("retry_count") or 0) + 1
    return {
        "current_node": "pivot_rerun",
        "retry_count": new_retry,
        "gate_decision": None,  # reset so next validation gate starts clean
        "strategy_output": None,  # reset pillar 1 output
        "step_events": [_event("pivot_rerun", 1, f"Pivot #{new_retry} — re-running Pillar 1")],
    }


# ---------------------------------------------------------------------------
# Pillar 2 — Architecture
# ---------------------------------------------------------------------------


async def run_pillar_2(state: RunState) -> dict[str, Any]:
    """Pillar 2: Architecture & Tech Stack.  Stub — wired to AF-040."""
    return {
        "current_pillar": 2,
        "current_node": "run_pillar_2",
        "architecture_output": {
            "stub": True,
            "erd": {},
            "openapi": {},
            "stack": [],
            "cost_forecast_usd": 0,
        },
        "step_events": [_event("run_pillar_2", 2, "Pillar 2 stub complete")],
    }


async def architecture_gate(state: RunState) -> dict[str, Any]:
    """HITL gate — architecture approval."""
    decision = state.get("gate_decision") or "pending"
    return {
        "current_node": "architecture_gate",
        "step_events": [_event("architecture_gate", 2, f"Gate decision processed: {decision}")],
    }


# ---------------------------------------------------------------------------
# Pillar 3 — Code Generation
# ---------------------------------------------------------------------------


async def run_pillar_3(state: RunState) -> dict[str, Any]:
    """Pillar 3: Autonomous Code Generation.  Stub — wired to AF-041."""
    return {
        "current_pillar": 3,
        "current_node": "run_pillar_3",
        "code_output": {"stub": True, "repo_url": None},
        "step_events": [_event("run_pillar_3", 3, "Pillar 3 stub complete")],
    }


# ---------------------------------------------------------------------------
# Pillar 4 — Testing & Self-Healing
# ---------------------------------------------------------------------------


async def run_pillar_4(state: RunState) -> dict[str, Any]:
    """Pillar 4: Testing & Self-Healing.  Stub — wired to AF-042."""
    return {
        "current_pillar": 4,
        "current_node": "run_pillar_4",
        "review_output": {"stub": True, "coverage": 0.0, "issues": [], "cycles": 0},
        "step_events": [_event("run_pillar_4", 4, "Pillar 4 stub complete")],
    }


# ---------------------------------------------------------------------------
# Pillar 5 — Deployment
# ---------------------------------------------------------------------------


async def run_pillar_5(state: RunState) -> dict[str, Any]:
    """Pillar 5: Deployment & Infrastructure. Wired to DevOpsAgent (AF-043).

    Gated on a real CoderOutput from Pillar 4. If upstream is a stub (pillars 3/4
    not yet wired), returns a stub deployment_output unchanged. When real data
    arrives, constructs a DevOpsState and invokes DevOpsAgent.run().
    """
    review_output = state.get("review_output") or {}
    code_output = state.get("code_output") or {}

    # Gate: upstream pillars must have produced real output.
    if review_output.get("stub") or code_output.get("stub") or not code_output:
        return {
            "current_pillar": 5,
            "current_node": "run_pillar_5",
            "deployment_output": {
                "stub": True,
                "deploy_url": None,
                "infra_cost_usd": 0,
            },
            "step_events": [
                _event("run_pillar_5", 5, "Pillar 5 stub — upstream CoderOutput not real yet"),
            ],
        }

    from app.agents._providers import GeminiRouter, JinjaPromptRegistry
    from app.agents.devops import DevOpsAgent
    from app.agents.devops.tools import LocalToolRegistry
    from app.core.config import get_settings
    from app.core.security import Principal
    from app.db.redis_pool import get_redis
    from app.db.session import SessionLocal
    from app.db.udal import UDAL
    from app.orchestrator.checkpointer import DualCheckpointer

    settings = get_settings()

    try:
        redis_client = get_redis()
    except RuntimeError:
        redis_client = None

    principal = Principal(organization_id=state["organization_id"], role="system")

    async with SessionLocal() as db_session:
        udal = UDAL(principal=principal, session=db_session, redis=redis_client)
        checkpointer = DualCheckpointer(session_factory=SessionLocal, redis=redis_client)
        tool_registry = LocalToolRegistry()
        prompt_registry = JinjaPromptRegistry()
        # GeminiRouter is constructed but not yet called by DevOps scaffold nodes.
        llm_router = GeminiRouter(
            api_key=settings.gemini_api_key, default_model=settings.strategy_model
        )

        agent = DevOpsAgent(
            udal=udal,
            checkpointer=checkpointer,
            tool_registry=tool_registry,
            prompt_registry=prompt_registry,
            llm_router=llm_router,
        )

        # Build DevOpsState input from upstream CoderOutput + tenant config.
        agent_input: dict[str, Any] = {
            **code_output,
            "run_id": state["run_id"],
            "organization_id": state["organization_id"],
            "parent_run_id": code_output.get("run_id", state["run_id"]),
            "grandparent_run_id": code_output.get("parent_run_id", state["run_id"]),
            "aws_region": code_output.get("aws_region", settings.foundation_aws_region),
            "repo_url": code_output.get("repo_url", code_output.get("github_repo_html_url", "")),
        }

        try:
            output_state = await agent.run(agent_input)
            output_dict = output_state.model_dump(mode="json")
            return {
                "current_pillar": 5,
                "current_node": "run_pillar_5",
                "deployment_output": {
                    "live_url": output_state.live_url,
                    "deploy_status": str(output_state.deploy_status),
                    "smoke_passed": output_state.smoke_tests_passed,
                    "monthly_cost_usd": output_state.estimated_monthly_cost_usd,
                    "deployment_id": output_state.deployment_id,
                    "full_state": output_dict,
                },
                "step_events": [
                    _event("run_pillar_5", 5, "Pillar 5 DevOpsAgent execution successful"),
                ],
            }
        except Exception as e:
            return {
                "current_pillar": 5,
                "current_node": "run_pillar_5",
                "status": "failed",
                "error": f"DevOpsAgent run failed: {str(e)}",
                "step_events": [
                    _event("run_pillar_5", 5, f"DevOpsAgent run failed: {str(e)}"),
                ],
            }


async def infra_spend_gate(state: RunState) -> dict[str, Any]:
    """HITL gate — triggered when infra cost exceeds threshold."""
    decision = state.get("gate_decision") or "pending"
    return {
        "current_node": "infra_spend_gate",
        "step_events": [_event("infra_spend_gate", 5, f"Gate decision processed: {decision}")],
    }


# ---------------------------------------------------------------------------
# Pillar 6 — Marketing & Launch
# ---------------------------------------------------------------------------


async def run_pillar_6(state: RunState) -> dict[str, Any]:
    """Pillar 6: Marketing & Launch Automation.  Stub — wired to AF-044."""
    return {
        "current_pillar": 6,
        "current_node": "run_pillar_6",
        "marketing_output": {
            "stub": True,
            "landing_page": None,
            "brand_kit": None,
            "social_posts": [],
        },
        "step_events": [_event("run_pillar_6", 6, "Pillar 6 stub complete")],
    }


async def launch_gate(state: RunState) -> dict[str, Any]:
    """HITL gate — Launch Control Center approval."""
    decision = state.get("gate_decision") or "pending"
    return {
        "current_node": "launch_gate",
        "step_events": [_event("launch_gate", 6, f"Gate decision processed: {decision}")],
    }


# ---------------------------------------------------------------------------
# Pillar 7 — LLMOps & Continuous Learning
# ---------------------------------------------------------------------------


async def run_pillar_7(state: RunState) -> dict[str, Any]:
    """Pillar 7: LLMOps & Continuous Learning.  Stub — wired to AF-045."""
    return {
        "current_pillar": 7,
        "current_node": "run_pillar_7",
        "status": "completed",
        "llmops_output": {"stub": True, "cost_report": {}, "eval_scores": {}},
        "step_events": [_event("run_pillar_7", 7, "Pipeline complete — all 7 pillars done")],
    }
