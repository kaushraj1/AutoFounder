"""AF-045 LLMOps Agent (Pillar 7).

Runs on a weekly cycle, analyzing execution traces from all other agents
and producing prompt optimizations, model routing updates, drift alerts,
and a FinOps report.

Pure LLM synthesis — no external tool calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from typing import Any

from jinja2 import Template

from app.agents.base import BaseAgent
from app.agents.llmops.schema import (
    AgentTrace,
    DriftAlert,
    FinOpsReport,
    LLMOpsInput,
    LLMOpsOutput,
    ModelRoutingUpdate,
    PromptOptimization,
)

logger = logging.getLogger("app.agents.llmops")

_CACHE_TTL = 3_600  # 1 h (matches SLA)
_CACHE_PREFIX = "llmops"
_COST_PER_1K_TOKENS = 0.001  # $0.001 / 1 K tokens (rough blended estimate)
_DRIFT_WARNING_PCT = 10.0
_DRIFT_CRITICAL_PCT = 25.0
_TOP_EXPENSIVE_RUNS = 5


class LLMOpsAgent(BaseAgent[LLMOpsInput, LLMOpsOutput]):
    """Pillar 7 — LLMOps: trace analysis, prompt optimisation, FinOps.

    Staged LLM analysis:
      _analyze_traces → _optimize_prompts → _detect_drift (computed) → _compute_finops
    """

    PILLAR = 7
    AGENT_ID = "llmops"
    SLA_SECONDS = 3600  # 1-hour weekly cycle

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def understand(self, input: LLMOpsInput) -> dict[str, Any]:
        """Validate input; build cache key; surface intent."""
        if not input.traces:
            logger.warning(
                "LLMOpsAgent received empty traces for run %s — analysis will produce empty report",
                input.run_id,
            )

        agent_ids = sorted({t.agent_id for t in input.traces})
        cache_key = self._cache_key(input)

        return {
            "run_id": input.run_id,
            "organization_id": input.organization_id,
            "analysis_period_days": input.analysis_period_days,
            "traces": input.traces,
            "agent_ids": agent_ids,
            "cache_key": cache_key,
        }

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Check Redis cache; short-circuit on hit."""
        cache_key = intent["cache_key"]
        try:
            cached = await self.udal.cache.get_session(cache_key)
            if cached:
                logger.info("LLMOps cache HIT for run %s", intent["run_id"])
                return {**intent, "cache_hit": True, "cached_output": cached}
        except Exception:
            pass
        return {**intent, "cache_hit": False}

    async def execute(self, plan: dict[str, Any]) -> LLMOpsOutput:
        """Staged LLM analysis: traces → prompt opts → drift → finops → summary."""
        if plan.get("cache_hit"):
            return LLMOpsOutput.model_validate(plan["cached_output"])

        traces: list[AgentTrace] = plan["traces"]
        agent_ids: list[str] = plan["agent_ids"]
        total_tokens = 0

        # Stage 1: Analyze traces via LLM
        findings, tokens = await self._analyze_traces(
            traces, agent_ids, plan["analysis_period_days"]
        )
        total_tokens += tokens

        # Stage 2: Optimize prompts per agent (LLM)
        optimizations: list[PromptOptimization] = []
        for agent_id in agent_ids:
            agent_traces = [t for t in traces if t.agent_id == agent_id]
            opts, tokens = await self._optimize_prompts(agent_id, agent_traces)
            optimizations.extend(opts)
            total_tokens += tokens

        # Stage 3: Detect metric drift (computed, no LLM)
        drift_alerts = self._detect_drift(traces)

        # Stage 4: Compute FinOps report (computed + LLM narrative)
        finops_report, tokens = await self._compute_finops(traces, plan["analysis_period_days"])
        total_tokens += tokens

        # Stage 5: Build summary markdown from findings
        summary_markdown = self._build_summary(
            findings, optimizations, drift_alerts, finops_report
        )

        output = LLMOpsOutput(
            run_id=plan["run_id"],
            organization_id=plan["organization_id"],
            prompt_optimizations=optimizations,
            routing_updates=self._build_routing_updates(findings),
            drift_alerts=drift_alerts,
            finops_report=finops_report,
            summary_markdown=summary_markdown,
            total_llm_tokens_used=total_tokens,
        )

        try:
            await self.udal.cache.set_session(
                plan["cache_key"], output.model_dump(), ttl=_CACHE_TTL
            )
        except Exception:
            pass

        return output

    async def verify(self, output: LLMOpsOutput) -> dict[str, Any]:
        """Verify FinOps report has cost data and summary is non-empty."""
        issues: list[str] = []

        if output.finops_report.total_cost_usd < 0:
            issues.append("finops_report.total_cost_usd is negative")

        if not output.summary_markdown.strip():
            issues.append("summary_markdown is empty")

        if output.finops_report.total_tokens < 0:
            issues.append("finops_report.total_tokens is negative")

        passed = len(issues) == 0
        if not passed:
            logger.warning(
                "LLMOps verify FAILED for run %s: %s",
                output.run_id,
                "; ".join(issues),
            )

        return {
            "passed": passed,
            "issues": issues,
            "drift_alert_count": len(output.drift_alerts),
            "optimization_count": len(output.prompt_optimizations),
        }

    async def learn(self, trace: dict[str, Any]) -> None:
        """Emit telemetry to observability layer."""
        raw_output = trace.get("output")
        tokens = 0
        n_optimizations = 0
        n_alerts = 0

        if isinstance(raw_output, LLMOpsOutput):
            tokens = raw_output.total_llm_tokens_used
            n_optimizations = len(raw_output.prompt_optimizations)
            n_alerts = len(raw_output.drift_alerts)
        elif isinstance(raw_output, dict):
            tokens = raw_output.get("total_llm_tokens_used", 0)
            n_optimizations = len(raw_output.get("prompt_optimizations", []))
            n_alerts = len(raw_output.get("drift_alerts", []))

        logger.info(
            "LLMOps run %s | org=%s | optimizations=%d | drift_alerts=%d | tokens=%d",
            trace.get("run_id"),
            trace.get("organization_id"),
            n_optimizations,
            n_alerts,
            tokens,
        )

    # ------------------------------------------------------------------
    # Private: staged analysis
    # ------------------------------------------------------------------

    async def _analyze_traces(
        self,
        traces: list[AgentTrace],
        agent_ids: list[str],
        period_days: int,
    ) -> tuple[dict[str, Any], int]:
        """Stage 1: LLM analysis of trace patterns and anomalies."""
        if not traces:
            return {"findings": [], "top_issues": []}, 0

        traces_summary = self._build_traces_summary(traces)
        raw_template = self.prompts.get("llmops/analyze_traces")
        rendered = Template(raw_template).render(
            traces_summary=traces_summary,
            period_days=period_days,
            agent_ids=agent_ids,
        )
        raw = await self._call_llm(
            task_class="llmops_analysis", prompt=rendered, json_mode=True
        )
        data = self._parse_json(raw, "analyze_traces")
        tokens = self._count_tokens(rendered, raw)
        return data if isinstance(data, dict) else {"findings": [], "top_issues": []}, tokens

    async def _optimize_prompts(
        self,
        agent_id: str,
        agent_traces: list[AgentTrace],
    ) -> tuple[list[PromptOptimization], int]:
        """Stage 2: LLM-suggested prompt improvements per agent."""
        if not agent_traces:
            return [], 0

        # Build current metrics summary
        verify_pass_rate = sum(1 for t in agent_traces if t.verify_passed) / len(agent_traces)
        avg_tokens = sum(t.tokens_used for t in agent_traces) / len(agent_traces)
        avg_coverage = (
            sum(t.coverage_score for t in agent_traces if t.coverage_score is not None)
            / max(1, sum(1 for t in agent_traces if t.coverage_score is not None))
        )
        current_metrics = {
            "verify_pass_rate": round(verify_pass_rate, 3),
            "avg_tokens_per_run": round(avg_tokens, 1),
            "avg_coverage_score": round(avg_coverage, 3),
            "total_runs_analyzed": len(agent_traces),
            "error_runs": sum(1 for t in agent_traces if t.error_count > 0),
        }

        # Sample up to 10 traces for the prompt (keep it concise)
        sample = agent_traces[:10]
        trace_samples = [
            {
                "run_id": t.run_id,
                "tokens_used": t.tokens_used,
                "elapsed_seconds": t.elapsed_seconds,
                "verify_passed": t.verify_passed,
                "error_count": t.error_count,
                "coverage_score": t.coverage_score,
                "timestamp": t.timestamp,
            }
            for t in sample
        ]

        raw_template = self.prompts.get("llmops/optimize_prompts")
        rendered = Template(raw_template).render(
            agent_id=agent_id,
            trace_samples=json.dumps(trace_samples, indent=2),
            current_metrics=json.dumps(current_metrics, indent=2),
        )
        raw = await self._call_llm(
            task_class="llmops_analysis", prompt=rendered, json_mode=True
        )
        data = self._parse_json(raw, f"optimize_prompts:{agent_id}")
        tokens = self._count_tokens(rendered, raw)

        if not isinstance(data, dict):
            return [], tokens

        optimizations: list[PromptOptimization] = []
        for item in data.get("optimizations", []):
            try:
                optimizations.append(
                    PromptOptimization(
                        agent_id=agent_id,
                        template_name=item.get("template_name", f"{agent_id}/unknown"),
                        current_score=current_metrics["avg_coverage_score"],
                        optimized_prompt_snippet=item.get("optimized_snippet", ""),
                        improvement_delta=float(item.get("improvement_delta", 0.0)),
                        recommendation=item.get("recommendation", "test"),
                    )
                )
            except Exception as exc:
                logger.warning("Skipping malformed optimization for %s: %s", agent_id, exc)

        return optimizations, tokens

    def _detect_drift(self, traces: list[AgentTrace]) -> list[DriftAlert]:
        """Stage 3: Statistical drift detection — no LLM.

        Splits traces chronologically (first half = baseline, second half = current).
        Emits DriftAlert when drift exceeds threshold on key metrics.
        """
        if len(traces) < 4:
            # Not enough data to compute meaningful drift
            return []

        # Group traces by agent
        by_agent: dict[str, list[AgentTrace]] = defaultdict(list)
        for t in traces:
            by_agent[t.agent_id].append(t)

        alerts: list[DriftAlert] = []

        for agent_id, agent_traces in by_agent.items():
            # Sort chronologically by timestamp (ISO strings sort lexicographically)
            sorted_traces = sorted(agent_traces, key=lambda t: t.timestamp)
            mid = len(sorted_traces) // 2
            baseline_traces = sorted_traces[:mid]
            current_traces = sorted_traces[mid:]

            if not baseline_traces or not current_traces:
                continue

            # Metric 1: coverage_score
            baseline_cov = [
                t.coverage_score for t in baseline_traces if t.coverage_score is not None
            ]
            current_cov = [
                t.coverage_score for t in current_traces if t.coverage_score is not None
            ]
            if baseline_cov and current_cov:
                b_avg = sum(baseline_cov) / len(baseline_cov)
                c_avg = sum(current_cov) / len(current_cov)
                alert = self._make_drift_alert(agent_id, "coverage_score", b_avg, c_avg)
                if alert:
                    alerts.append(alert)

            # Metric 2: verify_pass_rate
            b_pass = sum(1 for t in baseline_traces if t.verify_passed) / len(baseline_traces)
            c_pass = sum(1 for t in current_traces if t.verify_passed) / len(current_traces)
            alert = self._make_drift_alert(agent_id, "verify_pass_rate", b_pass, c_pass)
            if alert:
                alerts.append(alert)

            # Metric 3: avg_tokens (spike detection)
            b_tokens = sum(t.tokens_used for t in baseline_traces) / len(baseline_traces)
            c_tokens = sum(t.tokens_used for t in current_traces) / len(current_traces)
            alert = self._make_drift_alert(agent_id, "avg_tokens", b_tokens, c_tokens)
            if alert:
                alerts.append(alert)

        return alerts

    def _make_drift_alert(
        self,
        agent_id: str,
        metric: str,
        baseline: float,
        current: float,
    ) -> DriftAlert | None:
        """Return a DriftAlert if drift exceeds threshold, else None."""
        if baseline == 0.0:
            return None
        drift_pct = abs((current - baseline) / baseline) * 100.0
        if drift_pct < _DRIFT_WARNING_PCT:
            return None
        severity = "critical" if drift_pct >= _DRIFT_CRITICAL_PCT else "warning"
        return DriftAlert(
            agent_id=agent_id,
            metric=metric,
            baseline=round(baseline, 4),
            current=round(current, 4),
            drift_pct=round(drift_pct, 2),
            severity=severity,
        )

    async def _compute_finops(
        self,
        traces: list[AgentTrace],
        period_days: int,
    ) -> tuple[FinOpsReport, int]:
        """Stage 4: Computed cost aggregation + LLM narrative summary."""
        # --- Computed aggregation ---
        total_tokens = sum(t.tokens_used for t in traces)
        total_cost_usd = (total_tokens / 1_000) * _COST_PER_1K_TOKENS

        # Cost by agent
        tokens_by_agent: dict[str, int] = defaultdict(int)
        for t in traces:
            tokens_by_agent[t.agent_id] += t.tokens_used
        cost_by_agent: dict[str, float] = {
            aid: (tok / 1_000) * _COST_PER_1K_TOKENS
            for aid, tok in tokens_by_agent.items()
        }

        # Cost by org
        tokens_by_org: dict[str, int] = defaultdict(int)
        for t in traces:
            tokens_by_org[t.organization_id] += t.tokens_used
        cost_by_org: dict[str, float] = {
            org: (tok / 1_000) * _COST_PER_1K_TOKENS
            for org, tok in tokens_by_org.items()
        }

        # Top 5 most expensive runs by tokens_used
        top_runs = sorted(traces, key=lambda t: t.tokens_used, reverse=True)[:_TOP_EXPENSIVE_RUNS]
        top_expensive_runs = [
            {
                "run_id": t.run_id,
                "agent_id": t.agent_id,
                "organization_id": t.organization_id,
                "tokens_used": t.tokens_used,
                "estimated_cost_usd": round((t.tokens_used / 1_000) * _COST_PER_1K_TOKENS, 6),
            }
            for t in top_runs
        ]

        # --- LLM narrative ---
        avg_tokens = total_tokens / max(1, len(traces))
        top_agent = (
            max(tokens_by_agent, key=lambda k: tokens_by_agent[k])
            if tokens_by_agent
            else "none"
        )
        outlier_run_count = sum(
            1 for t in traces if t.tokens_used > (avg_tokens * 2)
        )

        cost_data = {
            "period": f"last_{period_days}_days",
            "total_cost_usd": total_cost_usd,
        }
        token_data = {
            "total_tokens": total_tokens,
            "avg_tokens_per_run": avg_tokens,
            "top_agent": top_agent,
            "outlier_run_count": outlier_run_count,
        }

        summary_markdown = ""
        savings_usd = 0.0
        llm_tokens = 0

        if traces:
            raw_template = self.prompts.get("llmops/generate_finops")
            rendered = Template(raw_template).render(
                cost_data=cost_data,
                token_data=token_data,
                agent_breakdown=cost_by_agent,
            )
            raw = await self._call_llm(
                task_class="llmops_analysis", prompt=rendered, json_mode=True
            )
            llm_tokens = self._count_tokens(rendered, raw)
            data = self._parse_json(raw, "generate_finops")
            if isinstance(data, dict):
                summary_markdown = data.get("summary_markdown", "")
                savings_usd = float(data.get("savings_usd", 0.0))

        if not summary_markdown:
            summary_markdown = (
                f"## FinOps Weekly Report\n\n"
                f"- **Period**: last {period_days} days\n"
                f"- **Total tokens**: {total_tokens:,}\n"
                f"- **Estimated cost**: ${total_cost_usd:.4f}\n"
            )

        report = FinOpsReport(
            period=f"last_{period_days}_days",
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost_usd, 6),
            cost_by_agent={k: round(v, 6) for k, v in cost_by_agent.items()},
            cost_by_org={k: round(v, 6) for k, v in cost_by_org.items()},
            top_expensive_runs=top_expensive_runs,
            optimization_savings_usd=round(savings_usd, 6),
        )
        return report, llm_tokens

    # ------------------------------------------------------------------
    # Private: routing updates
    # ------------------------------------------------------------------

    def _build_routing_updates(self, findings: dict[str, Any]) -> list[ModelRoutingUpdate]:
        """Derive model routing recommendations from trace findings.

        Phase 1: rule-based heuristics from LLM findings (no additional LLM call).
        """
        updates: list[ModelRoutingUpdate] = []
        for issue in findings.get("top_issues", []):
            issue_text = issue.get("issue", "").lower()
            agent_id = issue.get("agent_id", "")
            if "token" in issue_text and "expensive" in issue_text:
                updates.append(
                    ModelRoutingUpdate(
                        task_class=f"{agent_id}_generation",
                        current_model="gpt-4o",
                        recommended_model="gpt-4o-mini",
                        reason=(
                            f"Token outliers detected for {agent_id}; "
                            "cheaper model sufficient for this task class"
                        ),
                        expected_cost_delta_usd=-0.05,
                    )
                )
        return updates

    # ------------------------------------------------------------------
    # Private: summary
    # ------------------------------------------------------------------

    def _build_summary(
        self,
        findings: dict[str, Any],
        optimizations: list[PromptOptimization],
        drift_alerts: list[DriftAlert],
        finops: FinOpsReport,
    ) -> str:
        """Assemble top-level summary markdown from all analysis stages."""
        critical_alerts = [a for a in drift_alerts if a.severity == "critical"]
        promotes = [o for o in optimizations if o.recommendation == "promote"]

        lines = [
            "## LLMOps Weekly Summary",
            "",
            f"**Period**: {finops.period}  ",
            f"**Total cost**: ${finops.total_cost_usd:.4f}  ",
            f"**Total tokens**: {finops.total_tokens:,}  ",
            f"**Potential savings**: ${finops.optimization_savings_usd:.4f}",
            "",
        ]

        if critical_alerts:
            lines.append("### Critical Drift Alerts")
            for a in critical_alerts:
                lines.append(
                    f"- **{a.agent_id}** `{a.metric}`: baseline={a.baseline}, "
                    f"current={a.current}, drift={a.drift_pct:.1f}%"
                )
            lines.append("")

        top_issues = findings.get("top_issues", [])
        if top_issues:
            lines.append("### Top Issues")
            for issue in top_issues[:3]:
                lines.append(f"- **{issue.get('agent_id', '?')}**: {issue.get('issue', '')}")
                action = issue.get("recommended_action", "")
                if action:
                    lines.append(f"  - _Action_: {action}")
            lines.append("")

        if promotes:
            lines.append("### Prompt Optimizations Ready to Promote")
            for o in promotes:
                lines.append(
                    f"- **{o.agent_id}/{o.template_name}**: "
                    f"+{o.improvement_delta:.0%} improvement"
                )
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private: helpers
    # ------------------------------------------------------------------

    def _build_traces_summary(self, traces: list[AgentTrace]) -> str:
        """Build a compact text summary of trace stats per agent."""
        by_agent: dict[str, list[AgentTrace]] = defaultdict(list)
        for t in traces:
            by_agent[t.agent_id].append(t)

        lines = []
        for agent_id, agent_traces in sorted(by_agent.items()):
            total = len(agent_traces)
            passed = sum(1 for t in agent_traces if t.verify_passed)
            avg_tokens = sum(t.tokens_used for t in agent_traces) / total
            avg_elapsed = sum(t.elapsed_seconds for t in agent_traces) / total
            total_errors = sum(t.error_count for t in agent_traces)
            lines.append(
                f"{agent_id}: runs={total}, verify_pass_rate={passed/total:.0%}, "
                f"avg_tokens={avg_tokens:.0f}, avg_elapsed={avg_elapsed:.1f}s, "
                f"total_errors={total_errors}"
            )
        return "\n".join(lines)

    def _cache_key(self, input: LLMOpsInput) -> str:
        payload = f"{input.run_id}:{input.organization_id}:{input.analysis_period_days}"
        digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return f"{_CACHE_PREFIX}:{digest}"

    def _parse_json(self, raw: str, stage: str) -> Any:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            lines = lines[1:] if lines[0].startswith("```") else lines
            lines = lines[:-1] if lines and lines[-1].startswith("```") else lines
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except Exception as exc:
            logger.error(
                "JSON parse failed at stage '%s': %s — raw: %.200s", stage, exc, raw
            )
            return {} if stage in ("analyze_traces", "generate_finops") else []

    @staticmethod
    def _count_tokens(prompt: str, response: str) -> int:
        """Rough token estimate (4 chars/token) for LLMOps telemetry."""
        return (len(prompt) + len(response)) // 4
