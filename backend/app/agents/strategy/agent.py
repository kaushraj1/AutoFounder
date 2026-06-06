import logging
import uuid
from typing import Any

from app.agents.base import BaseAgent, VerifyError
from app.agents.strategy.graph import build_strategist_graph
from app.agents.strategy.schema import StrategistState

logger = logging.getLogger("app.agents.strategy")


class StrategyAgent(BaseAgent[Any, StrategistState]):
    """
    Strategy & Ideation Agent (Pillar 1).
    Coordinates market research and canvas compilation through LangGraph.
    """

    PILLAR = 1
    AGENT_ID = "strategy"
    SLA_SECONDS = 1800  # 30 minutes

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.graph = build_strategist_graph(self, self.checkpointer)

    async def understand(self, input_data: Any) -> dict[str, Any]:
        """Convert input parameters into validated raw idea details."""
        if isinstance(input_data, dict):
            idea_raw = input_data.get("idea_text") or input_data.get("idea_raw") or ""
            org_id = input_data.get("organization_id") or "default-org"
            run_id = input_data.get("run_id")
        else:
            idea_raw = getattr(input_data, "idea_raw", getattr(input_data, "idea_text", ""))
            org_id = getattr(input_data, "organization_id", "default-org")
            run_id = getattr(input_data, "run_id", None)

        if not idea_raw or len(idea_raw.strip()) < 10:
            raise ValueError("Raw idea is empty or too short (must be >= 10 characters)")

        return {
            "organization_id": org_id,
            "idea_raw": idea_raw,
            "run_id": run_id,
        }

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Formulate execution plan containing the initial graph state."""
        run_uuid = intent.get("run_id")
        if not run_uuid:
            run_uuid = uuid.uuid4()
        elif isinstance(run_uuid, str):
            try:
                run_uuid = uuid.UUID(run_uuid)
            except ValueError:
                run_uuid = uuid.uuid4()

        initial_state = StrategistState(
            run_id=run_uuid,
            organization_id=intent["organization_id"],
            idea_raw=intent["idea_raw"],
        )
        return {"initial_state": initial_state}

    async def execute(self, plan: dict[str, Any]) -> StrategistState:
        """Invoke compiled LangGraph state graph with plan data."""
        initial_state = plan["initial_state"]
        config = {"configurable": {"thread_id": str(initial_state.run_id)}}

        # Execute using thread-safe state graph checkpointer
        result = await self.graph.ainvoke(initial_state.model_dump(), config=config)
        return StrategistState.model_validate(result)

    async def verify(self, output: StrategistState) -> dict[str, Any]:
        """Verify report outputs conform to completeness constraints.

        Hard requirements (canvas, viability, report, no fatal error) raise
        ``VerifyError`` so a failed run never surfaces as a valid validation
        package. Citation groundedness is advisory — logged, not fatal.
        """
        issues = []
        if output.fatal_error:
            issues.append(f"Fatal error during execution: {output.fatal_error}")
        if not output.lean_canvas:
            issues.append("Lean Canvas was not generated")
        if not output.viability_score:
            issues.append("Viability score was not calculated")
        if not output.report_markdown:
            issues.append("Report markdown was not rendered")

        # Groundedness — advisory only (low-confidence flag, not a hard failure).
        sources = output.market_size.sources if output.market_size else []
        if not sources:
            logger.warning(
                "Strategy run %s produced no citations — low groundedness",
                output.run_id,
            )

        if issues:
            raise VerifyError(
                "; ".join(issues),
                agent_id=self.AGENT_ID,
                run_id=str(output.run_id),
            )

        return {"passed": True, "issues": []}

    async def learn(self, trace: dict[str, Any]) -> None:
        """Emit execution trace information for continuous learning loops."""
        logger.info(
            "Strategy run %s completed. Steps traced: %d. LLM Tokens: %d.",
            trace.get("run_id"),
            len(trace.get("steps", [])),
            trace.get("output", {}).get("total_llm_tokens_used", 0)
            if isinstance(trace.get("output"), dict)
            else 0,
        )
