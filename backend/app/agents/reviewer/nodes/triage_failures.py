"""Node 10 — triage_failures: classify results and route the loop (plan §3.4).

The DECISION is computed deterministically in code (safety-critical) — the LLM is
used only to enrich the human-readable failure list. Decision precedence:
  1. OWASP CRITICAL/HIGH hard-block (un-fixable)  → escalate  (D4, never approve)
  2. fixable issues remain & cycles left           → heal
  3. fixable issues remain & cycles exhausted      → escalate
  4. coverage < 80%                                → escalate  (D6, no net-new tests)
  5. judge did not approve                         → escalate
  6. otherwise                                     → approved
"""

from __future__ import annotations

import logging
from typing import Any

from jinja2 import Template

from app.agents.reviewer import metrics
from app.agents.reviewer.schema import (
    COVERAGE_THRESHOLD,
    MAX_HEAL_CYCLES,
    GateStatus,
    ReviewDecision,
    ReviewerState,
)
from app.agents.reviewer.utils.llm_parse import loads_lenient
from app.agents.reviewer.utils.owasp import collect_hard_blocks, owasp_violation_labels
from app.agents.reviewer.utils.retry import with_retry

logger = logging.getLogger("app.agents.reviewer.nodes.triage_failures")


@with_retry("triage_failures")
async def triage_failures(state: ReviewerState, agent: Any) -> dict[str, Any]:
    failures = _collect_failures(state)
    tokens = await _enrich_with_llm(state, agent, failures)
    failures = list(dict.fromkeys(failures))  # de-dupe, preserve order

    decision, reason, owasp_labels = _decide(state)

    result: dict[str, Any] = {
        "review_decision": decision,
        "current_failures": failures,
        "owasp_violations": owasp_labels,
        "total_llm_tokens_used": state.total_llm_tokens_used + tokens,
    }
    if decision is ReviewDecision.ESCALATE:
        result["escalation_reason"] = reason
    elif decision is ReviewDecision.APPROVED:
        result["is_approved"] = True

    logger.info("Triage decision=%s reason=%s (cycle %d)", decision, reason, state.heal_cycle)
    return result


def _collect_failures(state: ReviewerState) -> list[str]:
    failures: list[str] = []
    for lint in state.lint_results:
        if lint.status is GateStatus.FAILED and lint.error_count:
            failures.append(f"{lint.tool}: {lint.error_count} error(s)")
            failures.extend(lint.messages[:10])
    if state.unit_test_result and state.unit_test_result.status is GateStatus.FAILED:
        for f in state.unit_test_result.failures[:15]:
            failures.append(f"unit test failed: {f.test_id} — {f.message}")
    if state.e2e_test_result and state.e2e_test_result.status is GateStatus.FAILED:
        for f in state.e2e_test_result.failures[:10]:
            failures.append(f"e2e failed: {f.test_id} — {f.message}")
    for finding in state.security_findings:
        if finding.auto_fixable and not finding.suppressed:
            failures.append(
                f"security ({finding.severity}) {finding.rule_id} in {finding.file_path}"
            )
    return failures


async def _enrich_with_llm(state: ReviewerState, agent: Any, failures: list[str]) -> int:
    """Best-effort LLM triage to add human-readable failures. Never fatal."""
    try:
        rendered = Template(agent.prompts.get("reviewer/triage_failures")).render(
            heal_cycle=state.heal_cycle,
            max_heal_cycles=MAX_HEAL_CYCLES,
            llm_judge_score=state.llm_judge_score,
            lint_results=state.lint_results,
            unit_test_result=state.unit_test_result,
            e2e_test_result=state.e2e_test_result,
            security_findings=state.security_findings,
        )
        raw = await agent._call_llm(task_class="reviewer_triage", prompt=rendered, json_mode=True)
        data = loads_lenient(raw)
        if isinstance(data, dict):
            for item in data.get("failures", [])[:20]:
                failures.append(str(item))
        return (len(rendered) + len(raw)) // 4
    except Exception as exc:  # noqa: BLE001 - enrichment is advisory
        logger.warning("Triage LLM enrichment failed (non-fatal): %s", exc)
        return 0


def _decide(state: ReviewerState) -> tuple[ReviewDecision, str, list[str]]:
    # 1. OWASP hard block — never approve, never heal.
    hard_blocks = collect_hard_blocks(state.security_findings)
    if hard_blocks:
        labels = owasp_violation_labels(state.security_findings)
        for finding in hard_blocks:
            owasp = str(finding.owasp_category) if finding.owasp_category else "unmapped"
            metrics.OWASP_BLOCKS.labels(owasp=owasp).inc()
        return (
            ReviewDecision.ESCALATE,
            f"{len(hard_blocks)} unresolved CRITICAL/HIGH security finding(s) (OWASP hard block)",
            labels,
        )

    # 2/3. Fixable issues → heal while cycles remain, else escalate.
    if _has_fixable_issues(state):
        if state.heal_cycle < MAX_HEAL_CYCLES:
            return (ReviewDecision.HEAL, "fixable lint/test/dependency issues remain", [])
        return (
            ReviewDecision.ESCALATE,
            f"self-heal cycles exhausted ({MAX_HEAL_CYCLES}) with issues remaining",
            [],
        )

    # 4. Coverage gate (net-new test generation is out of MVP scope → escalate).
    unit = state.unit_test_result
    if unit and unit.coverage_pct is not None and unit.coverage_pct < COVERAGE_THRESHOLD:
        return (
            ReviewDecision.ESCALATE,
            f"unit-test coverage {unit.coverage_pct:.0f}% < {COVERAGE_THRESHOLD:.0f}% required",
            [],
        )

    # 5. Judge gate.
    if state.llm_judge_score is not None and not state.llm_judge_score.approved:
        return (ReviewDecision.ESCALATE, "LLM judge did not approve the code quality", [])

    # 6. All gates green.
    return (ReviewDecision.APPROVED, "all quality gates passed", [])


def _has_fixable_issues(state: ReviewerState) -> bool:
    lint_fixable = any(
        lint.status is GateStatus.FAILED and lint.fixable_count > 0 for lint in state.lint_results
    )
    unit_failed = bool(
        state.unit_test_result and state.unit_test_result.status is GateStatus.FAILED
    )
    e2e_failed = bool(state.e2e_test_result and state.e2e_test_result.status is GateStatus.FAILED)
    dep_fixable = any(f.auto_fixable and not f.suppressed for f in state.security_findings)
    return lint_fixable or unit_failed or e2e_failed or dep_fixable
