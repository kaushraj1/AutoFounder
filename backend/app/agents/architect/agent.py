"""ArchitectAgent — Pillar 2 (AF-040).

Implements the five-method BaseAgent loop around the LangGraph StateGraph.
Wired to real BaseAgent (AF-040 integration from base_stub to app.agents.base).

Platform usage:
    from app.agents.architect.agent import ArchitectAgent
    from app.agents.product_planner.schema import ProductPlannerOutput

    agent = ArchitectAgent(udal, checkpointer, tool_registry, prompt_registry, llm_router)
    result = await agent.run(initial_state)

Standalone (no platform DI) usage:
    from app.agents.architect.agent import ArchitectAgent
    from app.agents.architect.registry import ArchitectToolRegistry
    from app.agents._providers.jinja_prompt_registry import JinjaPromptRegistry
    from app.agents._providers.gemini_router import GeminiRouter

    tool_reg = ArchitectToolRegistry()
    prompt_reg = JinjaPromptRegistry()
    llm_router = GeminiRouter(api_key="...")
    agent = ArchitectAgent(None, None, tool_reg, prompt_reg, llm_router)
"""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID, uuid4

from app.agents.architect.graph import build_architect_graph
from app.agents.architect.schema import ArchitectOutput, FeatureList, Requirement
from app.agents.architect.state import ArchitectState
from app.agents.architect.tools.mermaid import MermaidTool
from app.agents.architect.tools.openapi_validate import OpenAPIValidateTool
from app.agents.base import (
    BaseAgent,
    GuardrailPipelineProtocol,
    LLMRouterProtocol,
    PromptRegistryProtocol,
    ToolRegistryProtocol,
)
from app.agents.product_planner.schema import ProductPlannerOutput
from app.agents.strategy.schema import StrategyOutput

logger = logging.getLogger(__name__)

_mermaid_tool = MermaidTool()
_openapi_tool = OpenAPIValidateTool()


class ArchitectAgent(BaseAgent[Any, ArchitectOutput]):
    """Pillar 2 — Architecture & Tech Stack Design agent.

    Wired to the real BaseAgent from app.agents.base (AF-040). Accepts full
    dependency injection: udal, checkpointer, tool_registry, prompt_registry,
    llm_router, and optional guardrails.
    """

    PILLAR = 2
    AGENT_ID = "architect"
    SLA_SECONDS = 900  # 15 min

    def __init__(
        self,
        udal: Any,
        checkpointer: Any,
        tool_registry: ToolRegistryProtocol,
        prompt_registry: PromptRegistryProtocol,
        llm_router: LLMRouterProtocol,
        *,
        breaker_failure_threshold: int = 5,
        breaker_reset_timeout: float = 30.0,
        guardrails: GuardrailPipelineProtocol | None = None,
    ) -> None:
        super().__init__(
            udal,
            checkpointer,
            tool_registry,
            prompt_registry,
            llm_router,
            breaker_failure_threshold=breaker_failure_threshold,
            breaker_reset_timeout=breaker_reset_timeout,
            guardrails=guardrails,
        )
        self._graph = build_architect_graph()

    # ------------------------------------------------------------------
    # Public entrypoint — call this instead of invoking the graph directly
    # ------------------------------------------------------------------

    async def run_pipeline(
        self,
        *,
        product_planner_output: ProductPlannerOutput,
        strategy_output: StrategyOutput,
        approval_status: str = "pending",
        rejection_comment: str | None = None,
    ) -> ArchitectOutput:
        """Run the full Architect Agent pipeline and return a typed output.

        Higher-level entry point that builds the initial ArchitectState and
        delegates to the BaseAgent run() loop (understand -> plan -> execute
        -> verify -> learn). For direct BaseAgent.run() usage pass the raw
        ArchitectState dict instead.

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
            "run_id": str(run_id),
            "organization_id": str(organization_id),
            "idea_normalised": strategy_output.idea_normalised,
            "viability_band": strategy_output.viability_band,
            "lean_canvas": strategy_output.lean_canvas.model_dump(),
            "prd": product_planner_output.prd_markdown,
            "approval_status": approval_status,
            "rejection_comment": rejection_comment,
            "errors": [],
            "llm_tokens_used": 0,
        }

        output = await self.run(initial_state)

        elapsed = time.monotonic() - start_time
        logger.info(
            "[architect] run=%s — done in %.1fs, approval=%s",
            run_id,
            elapsed,
            approval_status,
        )

        return output

    # ------------------------------------------------------------------
    # BaseAgent five-method loop
    # ------------------------------------------------------------------

    async def understand(self, input: Any) -> dict[str, Any]:
        """Parse the incoming state (built from ProductPlannerOutput) into a structured intent."""
        if isinstance(input, dict):
            input_state: dict[str, Any] = input
        else:
            # Support ArchitectState TypedDict or any dict-like
            input_state = dict(input)

        prd_preview = (input_state.get("prd") or "")[:200]
        summary = (
            f"Design architecture for: {input_state.get('idea_normalised', 'unknown idea')}. "
            f"Viability: {input_state.get('viability_band', 'unknown')}. "
            f"PRD preview: {prd_preview}..."
        )
        return {
            "summary": summary,
            "metadata": {
                "run_id": input_state.get("run_id"),
                "organization_id": input_state.get("organization_id"),
            },
            "input_state": input_state,
        }

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Decompose the intent into the 9-node execution plan."""
        return {
            **intent,
            "steps": [
                "extract_requirements",
                "design_erd || design_api_contract || select_stack",
                "design_join",
                "auth_strategy",
                "scaling_plan",
                "cost_forecast",
                "compose_featurelist",
                "hitl_gate",
            ],
        }

    async def execute(self, plan: dict[str, Any]) -> ArchitectOutput:
        """Run the LangGraph StateGraph and return the typed ArchitectOutput."""
        state: ArchitectState = plan.get("input_state", {})  # type: ignore[assignment]
        final_state: ArchitectState = self._graph.invoke(state)  # type: ignore[return-value]
        return self._state_to_output(final_state)

    async def verify(self, output: ArchitectOutput) -> dict[str, Any]:
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

        passed = len(issues) == 0
        if not passed:
            logger.warning("[architect] verify issues: %s", issues)

        return {"passed": passed, "issues": issues}

    async def learn(self, trace: dict[str, Any]) -> None:
        """Emit execution trace to LLMOps.

        Standalone: logs the trace.
        Production (Phase 2): publish to Kafka topic `architect.trace`.
        """
        output = trace.get("output")
        run_id = trace.get("run_id") or (
            getattr(output, "run_id", None) if output is not None else None
        )
        verify_passed: bool | None = None
        verify_issues: list[str] = []

        verify_result = trace.get("verify_result")
        if isinstance(verify_result, dict):
            verify_passed = verify_result.get("passed")
            verify_issues = verify_result.get("issues", [])

        logger.info(
            "[architect] trace — run=%s verify_passed=%s",
            run_id,
            verify_passed,
        )
        if verify_issues:
            logger.warning("[architect] trace verify issues: %s", verify_issues)
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
