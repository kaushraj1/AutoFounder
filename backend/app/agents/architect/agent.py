"""ArchitectAgent — Pillar 2 (AF-040).
  
Implements the five-method BaseAgent loop around the LangGraph StateGraph.

Standalone usage (no platform):
    from app.agents.architect.agent import ArchitectAgent
    from app.agents.product_planner.schema import ProductPlannerOutput
    import asyncio, json

    agent = ArchitectAgent()
    data = json.load(open("app/agents/architect/fixtures/saas_prd.json"))
    ppo = ProductPlannerOutput.model_validate(data["product_planner_output"])
    result = asyncio.run(agent.run(
        product_planner_output=ppo,
        approval_status="approved",   # skip HITL in tests
    ))
    print(result.model_dump_json(indent=2))

Platform integration (when AF-036 + AF-027 land):
    # 1. Change import in this file:
    #    from app.agents.architect.base_stub import BaseAgent, Intent, Plan, VerifyResult
    #    → from app.agents.base import Agent as BaseAgent, Intent, Plan, VerifyResult
    # 2. Replace the UDAL stubs in _persist_artifacts() with real UDAL calls.
    # 3. Replace the logger emit in learn() with a real Kafka/EventBridge emit.
    # Everything else stays identical.
"""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID, uuid4

from app.agents.architect.base_stub import BaseAgent, Intent, Plan, VerifyResult
from app.agents.architect.graph import build_architect_graph
from app.agents.architect.schema import ArchitectOutput, FeatureList, Requirement
from app.agents.architect.state import ArchitectState
from app.agents.architect.tools.mermaid import MermaidTool
from app.agents.architect.tools.openapi_validate import OpenAPIValidateTool
from app.agents.product_planner.schema import ProductPlannerOutput
from app.agents.strategy.schema import StrategyOutput

logger = logging.getLogger(__name__)

_mermaid_tool = MermaidTool()
_openapi_tool = OpenAPIValidateTool()


class ArchitectAgent(BaseAgent[Any, ArchitectOutput]):
    """Pillar 2 — Architecture & Tech Stack Design agent."""

    PILLAR = 2
    AGENT_ID = "architect"
    SLA_SECONDS = 900  # 15 min

    def __init__(self) -> None:
        self._graph = build_architect_graph()

    # ------------------------------------------------------------------
    # Public entrypoint — call this instead of invoking the graph directly
    # ------------------------------------------------------------------

    async def run(
        self,
        *,
        product_planner_output: ProductPlannerOutput,
        strategy_output: StrategyOutput,
        approval_status: str = "pending",
        rejection_comment: str | None = None,
    ) -> ArchitectOutput:
        """Run the full Architect Agent pipeline and return a typed output.

        Args:
            product_planner_output: Typed output from Pillar 1.5 (ProductPlannerAgent).
            strategy_output: Typed output from Pillar 1 (StrategyAgent) — carries
                lean_canvas, idea_normalised, and viability_band.
            approval_status: Pre-set to "approved" to skip HITL in tests.
            rejection_comment: Reason if status is "rejected".
        """
        run_id = product_planner_output.run_id
        organization_id = product_planner_output.organization_id
        start_time = time.monotonic()

        logger.info("[architect] run=%s org=%s — starting", run_id, organization_id)

        initial_state: ArchitectState = {
            "run_id": run_id,
            "organization_id": organization_id,
            "idea_normalised": strategy_output.idea_normalised,
            "viability_band": strategy_output.viability_band,
            "lean_canvas": strategy_output.lean_canvas.model_dump(),
            "prd": product_planner_output.prd_markdown,
            "approval_status": approval_status,
            "rejection_comment": rejection_comment,
            "errors": [],
            "llm_tokens_used": 0,
        }

        # ---- understand → plan → execute (all inside the graph) ----
        intent = await self.understand(initial_state)
        plan = await self.plan(intent)
        final_state: ArchitectState = await self.execute(plan, state=initial_state)

        # ---- verify output -----------------------------------------
        output = self._state_to_output(final_state)
        verify_result = await self.verify(output)

        if not verify_result.passed:
            logger.warning(
                "[architect] run=%s — verify issues: %s", run_id, verify_result.issues
            )

        # ---- learn (emit trace) ------------------------------------
        elapsed = time.monotonic() - start_time
        await self.learn({
            "run_id": run_id,
            "organization_id": organization_id,
            "pillar": self.PILLAR,
            "elapsed_seconds": round(elapsed, 2),
            "tokens_used": final_state.get("llm_tokens_used", 0),
            "errors": final_state.get("errors", []),
            "verify_passed": verify_result.passed,
            "verify_issues": verify_result.issues,
            "approval_status": final_state.get("approval_status"),
        })

        logger.info(
            "[architect] run=%s — done in %.1fs, tokens=%d, approval=%s",
            run_id,
            elapsed,
            final_state.get("llm_tokens_used", 0),
            final_state.get("approval_status"),
        )

        return output

    # ------------------------------------------------------------------
    # BaseAgent five-method loop
    # ------------------------------------------------------------------

    async def understand(self, input_state: ArchitectState) -> Intent:
        """Parse the incoming state (built from ProductPlannerOutput) into a structured intent."""
        prd_preview = (input_state.get("prd") or "")[:200]
        summary = (
            f"Design architecture for: {input_state.get('idea_normalised', 'unknown idea')}. "
            f"Viability: {input_state.get('viability_band', 'unknown')}. "
            f"PRD preview: {prd_preview}..."
        )
        return Intent(
            summary=summary,
            metadata={
                "run_id": input_state.get("run_id"),
                "organization_id": input_state.get("organization_id"),
            },
        )

    async def plan(self, intent: Intent) -> Plan:
        """Decompose the intent into the 9-node execution plan."""
        return Plan(steps=[
            "extract_requirements",
            "design_erd || design_api_contract || select_stack",
            "design_join",
            "auth_strategy",
            "scaling_plan",
            "cost_forecast",
            "compose_featurelist",
            "hitl_gate",
        ])

    async def execute(  # type: ignore[override]
        self, plan: Plan, *, state: ArchitectState
    ) -> ArchitectState:
        """Run the LangGraph StateGraph and return the final state."""
        return self._graph.invoke(state)  # type: ignore[return-value]

    async def verify(self, output: ArchitectOutput) -> VerifyResult:
        """Self-critique the ArchitectOutput before handing off downstream."""
        issues: list[str] = []

        # 1. ERD must be present and valid
        erd_result = _mermaid_tool.validate(output.erd_mermaid or "")
        if not erd_result.valid:
            issues.extend(f"ERD: {e}" for e in erd_result.errors)

        # 2. OpenAPI must be present and valid
        if output.openapi_3_1:
            oa_result = _openapi_tool.validate(output.openapi_3_1)
            if not oa_result.valid:
                issues.extend(f"OpenAPI: {e}" for e in oa_result.errors)
        else:
            issues.append("OpenAPI spec is missing")

        # 3. FeatureList must have features (FATAL for Pillar 6)
        if not output.feature_list or not output.feature_list.features:
            issues.append("FeatureList.features is empty — FATAL for Pillar 6")

        # 4. Stack must have core keys
        required_stack_keys = {"frontend", "backend", "database"}
        missing_keys = required_stack_keys - set(output.stack.keys())
        if missing_keys:
            issues.append(f"Stack missing keys: {missing_keys}")

        # 5. Requirements must exist
        if not output.requirements:
            issues.append("No requirements extracted")

        return VerifyResult(passed=len(issues) == 0, issues=issues)

    async def learn(self, trace: dict[str, Any]) -> None:
        """Emit execution trace to LLMOps.

        Standalone: logs the trace.
        Production (Phase 2): publish to Kafka topic `architect.trace`.
        """
        logger.info(
            "[architect] trace — run=%s elapsed=%.1fs tokens=%d verify_passed=%s",
            trace.get("run_id"),
            trace.get("elapsed_seconds", 0),
            trace.get("tokens_used", 0),
            trace.get("verify_passed"),
        )
        if trace.get("errors"):
            logger.warning("[architect] trace errors: %s", trace["errors"])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _state_to_output(self, state: ArchitectState) -> ArchitectOutput:
        """Convert the raw LangGraph state dict into a typed ArchitectOutput."""
        raw_fl = state.get("feature_list") or {}
        feature_list = FeatureList(
            features=raw_fl.get("features", []),
            integrations=raw_fl.get("integrations", []),
            pricing_tiers=raw_fl.get("pricing_tiers", []),
        )

        requirements = [
            Requirement(
                id=r.get("id", f"REQ-{i}"),
                kind=r.get("kind", "FR"),
                description=r.get("description", ""),
                priority=r.get("priority", "P1"),
            )
            for i, r in enumerate(state.get("requirements") or [])
        ]

        return ArchitectOutput(
            run_id=UUID(state.get("run_id") or str(uuid4())),
            organization_id=state.get("organization_id") or "unknown",
            requirements=requirements,
            erd_mermaid=state.get("erd_mermaid") or "",
            openapi_3_1=state.get("openapi_3_1") or {},
            stack=state.get("stack") or {},
            microservice_boundaries=state.get("microservice_boundaries") or [],
            auth_strategy=state.get("auth_strategy") or {},
            scaling_plan=state.get("scaling_plan") or {},
            cost_estimate=state.get("cost_estimate") or {},
            feature_list=feature_list,
            approval_status=state.get("approval_status") or "pending",
        )
