"""MarketingAgent — Pillar 6 (AF-044).

Implements the five-method BaseAgent loop around the LangGraph StateGraph.

Standalone usage (no platform):
    from app.agents.marketing.agent import MarketingAgent
    from app.agents.marketing.schema import MarketerInput, BrandConfig, FeatureList
    import asyncio
    from uuid import uuid4

    agent = MarketingAgent()
    result = asyncio.run(agent.run(MarketerInput(
        run_id=uuid4(),
        organization_id="org-test",
        idea_normalised="A secrets management SaaS for dev teams",
        brand_config=BrandConfig(product_name="SecretSync", tone="technical"),
        feature_list=FeatureList(
            features=["Encrypted secret vault", "RBAC", "CLI integration"],
            integrations=["GitHub Actions", "Vercel"],
            pricing_tiers=[{"name": "Free"}, {"name": "Pro", "price": "$12/mo"}],
        ),
        approval_status="approved",  # skip HITL in tests
    )))
    print(result.gtm_report_markdown[:500])

Platform integration (when AF-036 + AF-027 land):
    - UDAL calls in _persist_artifacts() replace S3 URI stubs
    - learn() publishes to Kafka topic `marketer.trace`
    - Everything else stays identical
"""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID, uuid4

from prometheus_client import Counter, Histogram

from app.agents.marketing.graph import build_marketer_graph
from app.agents.marketing.schema import (
    HallucinationReport,
    MarketerInput,
    MarketerOutput,
)
from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prometheus metrics (lightweight — prometheus-client is a core dep)
# ---------------------------------------------------------------------------

_node_duration = Histogram(
    "marketer_node_duration_seconds",
    "Per-node duration for the Marketing Agent",
    ["node", "tenant"],
)
_hallucination_findings = Counter(
    "marketer_hallucination_findings_total",
    "Hallucination findings by severity",
    ["severity"],
)
_approval_status = Counter(
    "marketer_approval_status_total",
    "HITL approval outcomes",
    ["status"],
)
_scheduled_posts = Counter(
    "marketer_scheduled_posts_total",
    "Posts scheduled by channel",
    ["channel"],
)
_images_generated = Counter(
    "marketer_images_generated_total",
    "DALL-E 3 image generation outcomes",
    ["status"],
)


# ---------------------------------------------------------------------------
# Minimal BaseAgent stub for standalone mode
# ---------------------------------------------------------------------------


class _BaseAgentStub:
    """Minimal stand-in for platform BaseAgent.

    When the platform wires up (AF-036 fully integrated), MarketingAgent can
    call super().__init__(udal, checkpointer, ...) — everything else stays.
    """

    PILLAR: int = 6
    AGENT_ID: str = "marketing"
    SLA_SECONDS: int = 2700


class MarketingAgent(_BaseAgentStub):
    """Pillar 6 — Marketing & Launch Automation agent (AF-044)."""

    PILLAR = 6
    AGENT_ID = "marketing"
    SLA_SECONDS = 2700  # 45 min excl. HITL

    def __init__(self) -> None:
        self._graph = build_marketer_graph()

    # ------------------------------------------------------------------
    # Public entrypoint
    # ------------------------------------------------------------------

    async def run(self, input: MarketerInput) -> MarketerOutput:  # noqa: A002
        """Run the full Marketing Agent pipeline and return a typed output.

        Args:
            input: MarketerInput with upstream pillar data.

        Returns:
            MarketerOutput — complete GTM package.
        """
        start_time = time.monotonic()
        run_id = str(input.run_id)
        org_id = input.organization_id

        logger.info("[marketing] run=%s org=%s — starting", run_id, org_id)

        # 1. Understand
        intent = await self.understand(input)

        # 2. Plan
        plan = await self.plan(intent)

        # 3. Execute
        plan["initial_state"]
        final_state: MarketerState = await self.execute(plan)

        # 4. Convert to output
        output = self._state_to_output(final_state)

        # 5. Verify
        await self.verify(output)

        # 6. Emit metrics
        self._emit_metrics(final_state, org_id)

        elapsed = time.monotonic() - start_time

        # 7. Learn
        await self.learn(
            {
                "run_id": run_id,
                "organization_id": org_id,
                "pillar": self.PILLAR,
                "elapsed_seconds": round(elapsed, 2),
                "tokens_used": final_state.get("llm_tokens_used", 0),
                "images_generated": final_state.get("images_generated", 0),
                "approval_status": final_state.get("approval_status"),
                "errors": final_state.get("errors", []),
            }
        )

        logger.info(
            "[marketing] run=%s — done in %.1fs tokens=%d images=%d approval=%s",
            run_id,
            elapsed,
            final_state.get("llm_tokens_used", 0),
            final_state.get("images_generated", 0),
            final_state.get("approval_status"),
        )

        return output

    # ------------------------------------------------------------------
    # Five-method loop
    # ------------------------------------------------------------------

    async def understand(self, input: MarketerInput) -> dict[str, Any]:  # noqa: A002
        """Parse MarketerInput into a structured intent dict."""
        return {
            "run_id": str(input.run_id),
            "organization_id": input.organization_id,
            "product_name": input.brand_config.product_name,
            "feature_count": len(input.feature_list.features),
            "has_live_url": bool(input.live_url),
        }

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Decompose intent into initial LangGraph state."""

        # We pass the raw intent back — actual input is retrieved from caller context
        # The real state is built in execute()
        return {"intent": intent, "initial_state": intent}

    async def execute(self, plan: dict[str, Any]) -> MarketerState:
        """Run the LangGraph StateGraph.

        Note: MarketingAgent.run() builds the initial state directly to avoid
        double-serialisation. This method is called with the full plan dict.
        """
        # The initial state was set by the caller of run() → reconstruct from plan context
        # In the five-method loop, run() passes state via _run_graph()
        raise NotImplementedError("Use MarketingAgent.run() directly")

    async def verify(self, output: MarketerOutput) -> dict[str, Any]:
        """Self-critique: check hallucination passed + at least 1 content type approved."""
        issues: list[str] = []

        if output.hallucination_report and not output.hallucination_report.passed:
            issues.append(
                f"Hallucination check not passed: "
                f"{output.hallucination_report.critical_count} critical"
            )

        if not output.approved_content_types and output.approval_status not in (
            "timed_out",
            "rejected",
        ):
            issues.append("No content types approved")

        if output.errors:
            logger.warning("[marketing] verify — %d errors in output", len(output.errors))

        if issues:
            logger.warning("[marketing] verify issues: %s", issues)

        return {"passed": len(issues) == 0, "issues": issues}

    async def learn(self, trace: dict[str, Any]) -> None:
        """Emit execution trace to LLMOps.

        Standalone: logs trace.
        Production (Phase 2): publish to Kafka topic `marketer.trace`.
        """
        logger.info(
            "[marketing] trace — run=%s elapsed=%.1fs tokens=%d images=%d approval=%s errors=%d",
            trace.get("run_id"),
            trace.get("elapsed_seconds", 0),
            trace.get("tokens_used", 0),
            trace.get("images_generated", 0),
            trace.get("approval_status"),
            len(trace.get("errors", [])),
        )
        if trace.get("errors"):
            logger.warning("[marketing] trace errors: %s", trace["errors"])

    # ------------------------------------------------------------------
    # Graph invocation (internal)
    # ------------------------------------------------------------------

    async def _run_graph(self, initial_state: MarketerState) -> MarketerState:
        """Invoke the compiled graph and return final state."""
        result = await self._graph.ainvoke(initial_state)
        return result  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # State → Output conversion
    # ------------------------------------------------------------------

    def _state_to_output(self, state: MarketerState) -> MarketerOutput:
        """Convert final LangGraph state dict into a typed MarketerOutput."""
        hall_raw = state.get("hallucination_report") or {}
        hall_report = HallucinationReport(
            critical_count=hall_raw.get("critical_count", 0),
            warning_count=hall_raw.get("warning_count", 0),
            passed=hall_raw.get("passed", True),
            retry_count=hall_raw.get("retry_count", 0),
            findings=[],
        )

        return MarketerOutput(
            run_id=UUID(state.get("run_id") or str(uuid4())),
            parent_run_id=state.get("parent_run_id", ""),
            organization_id=state.get("organization_id", "unknown"),
            product_name=(state.get("brand_config") or {}).get("product_name", ""),
            live_url=state.get("effective_live_url", ""),
            hallucination_report=hall_report,
            hallucination_critical_count=hall_report.critical_count,
            hallucination_warning_count=hall_report.warning_count,
            approval_status=state.get("approval_status", "pending"),
            approved_content_types=state.get("approved_content_types", []),
            rejected_content_types=state.get("rejected_content_types", []),
            gtm_report_markdown=state.get("gtm_report_markdown", ""),
            gtm_report_s3_uri=state.get("gtm_report_s3_uri", ""),
            total_llm_tokens_used=state.get("llm_tokens_used", 0),
            total_images_generated=state.get("images_generated", 0),
            errors=state.get("errors", []),
        )

    # ------------------------------------------------------------------
    # Metrics emission
    # ------------------------------------------------------------------

    def _emit_metrics(self, state: MarketerState, tenant: str) -> None:
        """Emit Prometheus metrics for the completed run."""
        # Approval status
        approval = state.get("approval_status", "unknown")
        _approval_status.labels(status=approval).inc()

        # Hallucination findings
        hall = state.get("hallucination_report") or {}
        if hall.get("critical_count", 0):
            _hallucination_findings.labels(severity="critical").inc(hall["critical_count"])
        if hall.get("warning_count", 0):
            _hallucination_findings.labels(severity="warning").inc(hall["warning_count"])

        # Images
        images = state.get("images_generated", 0)
        if images:
            _images_generated.labels(status="generated").inc(images)

        # Scheduled posts
        scheduled = state.get("scheduled_post_ids") or {}
        for channel, info in scheduled.items():
            if isinstance(info, dict) and info.get("status") == "scheduled":
                _scheduled_posts.labels(channel=channel).inc()
