"""AF-042 Reviewer / Self-Healer Agent (Pillar 4).

Subclasses ``BaseAgent`` and drives a LangGraph ``StateGraph`` through the
understand → plan → execute → verify → learn loop. Execute runs the graph
(ingest → sandbox → parallel gates → judge → triage → heal loop → report).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.agents.base import BaseAgent, VerifyError
from app.agents.reviewer import metrics
from app.agents.reviewer.graph import build_reviewer_graph
from app.agents.reviewer.schema import (
    ReviewDecision,
    ReviewerInput,
    ReviewerState,
    SeverityLevel,
)
from app.agents.reviewer.utils.owasp import collect_hard_blocks

logger = logging.getLogger("app.agents.reviewer")

# Heal loop (≈10 supersteps/cycle × 5 cycles) + entry/exit headroom.
_RECURSION_LIMIT = 70


class ReviewerAgent(BaseAgent[Any, ReviewerState]):
    """Reviewer / Self-Healer Agent — quality gate + bounded self-heal loop."""

    PILLAR = 4
    AGENT_ID = "reviewer"
    SLA_SECONDS = 900  # 15 minutes (excl. human escalation)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.graph = build_reviewer_graph(self, self.checkpointer)

    async def understand(self, input_data: Any) -> dict[str, Any]:
        """Validate that there is a repository to review."""
        if isinstance(input_data, ReviewerInput):
            data = input_data.model_dump()
        elif isinstance(input_data, dict):
            data = dict(input_data)
        else:
            data = {
                "organization_id": getattr(input_data, "organization_id", ""),
                "repo_url": getattr(input_data, "repo_url", ""),
                "local_path": getattr(input_data, "local_path", None),
                "branch": getattr(input_data, "branch", "main"),
                "pr_number": getattr(input_data, "pr_number", 0),
                "coder_run_id": getattr(input_data, "coder_run_id", None),
                "run_id": getattr(input_data, "run_id", None),
                "feature_list": getattr(input_data, "feature_list", []),
            }

        if not data.get("repo_url") and not data.get("local_path"):
            raise ValueError("ReviewerInput requires repo_url or local_path")
        if not data.get("organization_id"):
            raise ValueError("ReviewerInput requires organization_id")
        return data

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Build the initial graph state from validated intent."""
        run_id = intent.get("run_id") or uuid.uuid4()
        if isinstance(run_id, str):
            try:
                run_id = uuid.UUID(run_id)
            except ValueError:
                run_id = uuid.uuid4()

        coder_run_id = intent.get("coder_run_id")
        if isinstance(coder_run_id, str):
            try:
                coder_run_id = uuid.UUID(coder_run_id)
            except ValueError:
                coder_run_id = None

        initial_state = ReviewerState(
            run_id=run_id,
            organization_id=intent["organization_id"],
            coder_run_id=coder_run_id,
            repo_url=intent.get("repo_url") or "",
            pr_number=int(intent.get("pr_number") or 0),
            branch=intent.get("branch") or "main",
            local_path=intent.get("local_path"),
            feature_list=list(intent.get("feature_list") or []),
        )
        return {"initial_state": initial_state}

    async def execute(self, plan: dict[str, Any]) -> ReviewerState:
        """Invoke the compiled graph with checkpointing + recursion budget."""
        initial_state: ReviewerState = plan["initial_state"]
        config = {
            "configurable": {"thread_id": str(initial_state.run_id)},
            "recursion_limit": _RECURSION_LIMIT,
        }
        result = await self.graph.ainvoke(initial_state.model_dump(), config=config)
        return ReviewerState.model_validate(result)

    async def verify(self, output: ReviewerState) -> dict[str, Any]:
        """Hard invariants: a decision exists and approvals are safe.

        An approved verdict must never carry an unresolved OWASP hard-block or
        sub-threshold coverage — those are defended in triage, but re-checked
        here so a corrupt run can't be presented as a green build.
        """
        issues: list[str] = []
        if output.review_decision is None:
            issues.append("No review decision was produced")

        if output.review_decision is ReviewDecision.APPROVED:
            hard_blocks = collect_hard_blocks(output.security_findings)
            if hard_blocks:
                issues.append(f"Approved despite {len(hard_blocks)} unresolved OWASP hard-block(s)")
            criticals = [
                f
                for f in output.security_findings
                if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH) and not f.suppressed
            ]
            if criticals:
                issues.append(
                    f"Approved with {len(criticals)} unresolved CRITICAL/HIGH security finding(s)"
                )
            unit = output.unit_test_result
            if unit is None:
                issues.append("Approved with no unit-test result (gate may have crashed)")
            elif unit.coverage_pct is not None and unit.coverage_pct < 80:
                issues.append(f"Approved with coverage {unit.coverage_pct:.0f}% < 80%")

        if issues:
            raise VerifyError("; ".join(issues), agent_id=self.AGENT_ID, run_id=str(output.run_id))
        return {"passed": True, "issues": []}

    async def learn(self, trace: dict[str, Any]) -> None:
        """Emit heal-cycle telemetry to the LLMOps loop."""
        output = trace.get("output")
        decision = "unknown"
        heal_cycles = 0
        tokens = 0
        if isinstance(output, ReviewerState):
            decision = str(output.review_decision or "unknown")
            heal_cycles = output.heal_cycle
            tokens = output.total_llm_tokens_used
        elif isinstance(output, dict):
            decision = str(output.get("review_decision", "unknown"))
            heal_cycles = int(output.get("heal_cycle", 0))
            tokens = int(output.get("total_llm_tokens_used", 0))

        if heal_cycles >= 4 and isinstance(output, ReviewerState):
            metrics.HIGH_HEAL_CYCLES.labels(tenant=output.organization_id).inc()
            logger.warning(
                "High heal cycles (%d) for run %s — flag Coder prompts for review",
                heal_cycles,
                trace.get("run_id"),
            )

        logger.info(
            "Reviewer run %s | decision=%s | heal_cycles=%d | tokens=%d",
            trace.get("run_id"),
            decision,
            heal_cycles,
            tokens,
        )
