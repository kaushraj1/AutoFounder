"""Unit — triage decision precedence (the safety-critical routing logic)."""

from __future__ import annotations

from tests.agents.reviewer.conftest import make_state

from app.agents.reviewer.nodes.triage_failures import _decide
from app.agents.reviewer.schema import (
    COVERAGE_THRESHOLD,
    MAX_HEAL_CYCLES,
    GateStatus,
    LintResult,
    OWASPCategory,
    ReviewDecision,
    SecurityFinding,
    SeverityLevel,
    TestSuiteResult,
)


def _owasp_finding() -> SecurityFinding:
    return SecurityFinding(
        tool="semgrep",
        severity=SeverityLevel.CRITICAL,
        rule_id="sqli",
        file_path="db.py",
        message="SQL injection",
        owasp_category=OWASPCategory.A03_INJECTION,
    )


def test_owasp_hard_block_escalates_even_with_other_signals() -> None:
    state = make_state(
        security_findings=[_owasp_finding()],
        unit_test_result=TestSuiteResult(
            runner="pytest", status=GateStatus.PASSED, coverage_pct=95
        ),
    )
    decision, reason, owasp = _decide(state)
    assert decision is ReviewDecision.ESCALATE
    assert "hard block" in reason.lower()
    assert owasp and "A03" in owasp[0]


def test_fixable_lint_with_cycles_left_heals() -> None:
    state = make_state(
        heal_cycle=0,
        lint_results=[
            LintResult(tool="ruff", status=GateStatus.FAILED, error_count=3, fixable_count=3)
        ],
    )
    decision, _, _ = _decide(state)
    assert decision is ReviewDecision.HEAL


def test_failing_tests_with_cycles_exhausted_escalates() -> None:
    state = make_state(
        heal_cycle=MAX_HEAL_CYCLES,
        unit_test_result=TestSuiteResult(runner="pytest", status=GateStatus.FAILED, failed=2),
    )
    decision, reason, _ = _decide(state)
    assert decision is ReviewDecision.ESCALATE
    assert "cycles exhausted" in reason.lower()


def test_low_coverage_escalates_when_no_fixable_issues() -> None:
    state = make_state(
        unit_test_result=TestSuiteResult(
            runner="pytest", status=GateStatus.PASSED, coverage_pct=62.0
        ),
    )
    decision, reason, _ = _decide(state)
    assert decision is ReviewDecision.ESCALATE
    assert "coverage" in reason.lower()
    assert str(int(COVERAGE_THRESHOLD)) in reason


def test_judge_rejection_escalates() -> None:
    from app.agents.reviewer.schema import LLMJudgeScore

    state = make_state(
        unit_test_result=TestSuiteResult(
            runner="pytest", status=GateStatus.PASSED, coverage_pct=92.0
        ),
        llm_judge_score=LLMJudgeScore(
            readability=90, maintainability=90, security_posture=90, overall=90, approved=False
        ),
    )
    decision, reason, _ = _decide(state)
    assert decision is ReviewDecision.ESCALATE
    assert "judge" in reason.lower()


def test_all_green_approves() -> None:
    from app.agents.reviewer.schema import LLMJudgeScore

    state = make_state(
        unit_test_result=TestSuiteResult(
            runner="pytest", status=GateStatus.PASSED, coverage_pct=92.0
        ),
        llm_judge_score=LLMJudgeScore(
            readability=90, maintainability=90, security_posture=90, overall=90, approved=True
        ),
    )
    decision, _, _ = _decide(state)
    assert decision is ReviewDecision.APPROVED
