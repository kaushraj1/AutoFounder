"""Node 13 — emit_report: assemble the report, persist it, comment on the PR (plan §3.4).

Reached on the APPROVED path. Always produces a report: the LLM writes the
narrative, but a deterministic fallback guarantees a report even if the model
call fails, so an approved run is never report-less.
"""

from __future__ import annotations

import logging
from typing import Any

from jinja2 import Template

from app.agents.reviewer import metrics
from app.agents.reviewer.persistence import persist_report
from app.agents.reviewer.schema import ReviewDecision, ReviewerState
from app.agents.reviewer.tools import github
from app.agents.reviewer.utils.redact import redact_url
from app.core.config import get_settings

logger = logging.getLogger("app.agents.reviewer.nodes.emit_report")


async def emit_report(state: ReviewerState, agent: Any) -> dict[str, Any]:
    settings = get_settings()
    markdown, tokens = await _build_report(state, agent)

    report_uri = await persist_report(
        agent.udal,
        run_id=str(state.run_id),
        org_id=state.organization_id,
        markdown=markdown,
        findings=state.security_findings,
    )
    comment_url = await github.post_pr_comment(
        state.repo_url,
        state.pr_number,
        markdown,
        token=settings.github_token or None,
    )

    is_approved = state.review_decision is ReviewDecision.APPROVED
    _record_metrics(state)

    return {
        "review_report_markdown": markdown,
        "review_report_uri": report_uri,
        "github_pr_comment_url": comment_url,
        "is_approved": is_approved,
        "is_complete": True,
        "total_llm_tokens_used": state.total_llm_tokens_used + tokens,
    }


async def _build_report(state: ReviewerState, agent: Any) -> tuple[str, int]:
    try:
        rendered = Template(agent.prompts.get("reviewer/emit_report")).render(
            repo_url=redact_url(state.repo_url),
            branch=state.branch,
            review_decision=state.review_decision,
            heal_cycle=state.heal_cycle,
            escalation_reason=state.escalation_reason,
            lint_results=state.lint_results,
            unit_test_result=state.unit_test_result,
            e2e_test_result=state.e2e_test_result,
            sonarqube_metrics=state.sonarqube_metrics,
            llm_judge_score=state.llm_judge_score,
            security_findings=state.security_findings,
            heal_history=state.heal_history,
        )
        raw = await agent._call_llm(task_class="reviewer_report", prompt=rendered)
        if raw and raw.strip():
            return raw, (len(rendered) + len(raw)) // 4
    except Exception as exc:  # noqa: BLE001 - fall back to deterministic report
        logger.warning("emit_report LLM failed, using fallback: %s", exc)
    return build_fallback_report(state), 0


def build_fallback_report(state: ReviewerState) -> str:
    """Deterministic Markdown report (no LLM) — always available."""
    unit = state.unit_test_result
    coverage = f"{unit.coverage_pct:.0f}%" if unit and unit.coverage_pct is not None else "n/a"
    lines = [
        f"# Code Review Report — {redact_url(state.repo_url)}",
        "",
        f"**Decision:** `{state.review_decision}`  ·  **Heal cycles:** {state.heal_cycle}",
        "",
    ]
    if state.escalation_reason:
        lines += [f"> **Escalation reason:** {state.escalation_reason}", ""]
    lint_summary = ", ".join(f"{lr.tool}={lr.status}" for lr in state.lint_results) or "n/a"
    unit_summary = f"{unit.passed}/{unit.total} passed, coverage {coverage}" if unit else "n/a"
    lines += [
        "## Test Summary",
        f"- Lint: {lint_summary}",
        f"- Unit: {unit_summary}",
        "",
        "## Security Audit",
    ]
    if state.security_findings:
        for f in state.security_findings:
            lines.append(f"- [{f.severity}] {f.tool}:{f.rule_id} {f.file_path} — {f.message}")
    else:
        lines.append("- No security findings.")
    if state.owasp_violations:
        lines += ["", "### OWASP hard blocks"]
        lines += [f"- {v}" for v in state.owasp_violations]
    lines += ["", "## Self-Heal Log"]
    if state.heal_history:
        for h in state.heal_history:
            files = ", ".join(h.files_patched) or "no files"
            lines.append(f"- cycle {h.cycle}: {h.outcome} ({files})")
    else:
        lines.append("- No heal cycles required.")
    return "\n".join(lines)


def _record_metrics(state: ReviewerState) -> None:
    # reviewer_high_heal_cycles_total is incremented once per run in ReviewerAgent.learn()
    # (which runs on every terminal path), so it is intentionally NOT counted here.
    decision = str(state.review_decision or ReviewDecision.APPROVED)
    metrics.DECISION.labels(decision=decision).inc()
    metrics.HEAL_CYCLES.labels(tenant=state.organization_id, decision=decision).observe(
        state.heal_cycle
    )
