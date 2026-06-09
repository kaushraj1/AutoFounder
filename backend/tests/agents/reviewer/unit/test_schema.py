"""Unit — schema validation + ReviewerOutput adapter."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents.reviewer.schema import (
    LLMJudgeScore,
    ReviewDecision,
    ReviewerOutput,
    ReviewerState,
    SecurityFinding,
    SeverityLevel,
    TestSuiteResult,
)


def test_coverage_validator_rejects_out_of_range() -> None:
    with pytest.raises(ValidationError):
        TestSuiteResult(runner="pytest", coverage_pct=150)


def test_judge_score_range_enforced() -> None:
    with pytest.raises(ValidationError):
        LLMJudgeScore(readability=120, maintainability=80, security_posture=70, overall=80)


def test_output_from_state_counts_criticals_and_coverage() -> None:
    state = ReviewerState(
        organization_id="org-1",
        repo_url="https://github.com/a/b",
        branch="main",
        pr_number=3,
        review_decision=ReviewDecision.ESCALATE,
        escalation_reason="owasp",
        unit_test_result=TestSuiteResult(runner="pytest", coverage_pct=72.0),
        security_findings=[
            SecurityFinding(
                tool="semgrep",
                severity=SeverityLevel.CRITICAL,
                rule_id="r1",
                file_path="x.py",
                message="m",
            ),
            SecurityFinding(
                tool="trivy",
                severity=SeverityLevel.LOW,
                rule_id="r2",
                file_path="y.py",
                message="m",
            ),
        ],
    )
    out = ReviewerOutput.from_state(state, completed_at_unix_ms=123)
    assert out.review_decision == "escalate"
    assert out.is_approved is False
    assert out.unit_test_coverage == 72.0
    assert out.security_finding_count == 2
    assert out.critical_finding_count == 1
    assert out.completed_at_unix_ms == 123


def test_output_defaults_to_escalate_when_no_decision() -> None:
    state = ReviewerState(organization_id="o", repo_url="r", branch="main")
    out = ReviewerOutput.from_state(state, completed_at_unix_ms=1)
    assert out.review_decision == "escalate"
