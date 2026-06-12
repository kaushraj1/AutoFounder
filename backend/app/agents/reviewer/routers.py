"""Conditional-edge routers for the Reviewer graph (plan §3.3, §4.1)."""

from __future__ import annotations

from app.agents.reviewer.schema import ReviewDecision, ReviewerState

# The five gates that fan out from spin_sandbox and converge at test_join.
PARALLEL_GATES = [
    "run_linters",
    "run_unit_tests",
    "run_e2e_tests",
    "run_security_scan",
    "run_sonarqube",
]


def route_after_ingest(state: ReviewerState) -> str:
    """Ingest → sandbox, or straight to the error sink on a fatal input."""
    return "error_handler" if state.fatal_error else "spin_sandbox"


def route_after_sandbox(state: ReviewerState) -> list[str]:
    """Fan out to the five parallel gates (or escalate on a sandbox build failure)."""
    if state.fatal_error:
        return ["error_handler"]
    return list(PARALLEL_GATES)


def route_after_join(state: ReviewerState) -> str:
    """Barrier → judge, unless a fatal error or a crashed safety-critical gate.

    A unit-test gate that crashed through all retries leaves ``unit_test_result``
    unset with a recorded fault — escalate rather than judge a coverage-blind
    build that could otherwise be approved by the absence of a result.
    """
    if state.fatal_error:
        return "error_handler"
    if state.unit_test_result is None and state.error_count > 0:
        return "error_handler"
    return "llm_judge"


def route_after_judge(state: ReviewerState) -> str:
    """Judge → triage, unless a fatal error occurred."""
    return "error_handler" if state.fatal_error else "triage_failures"


def route_after_triage(state: ReviewerState) -> str:
    """Triage decision → approve (teardown+report), heal (loop), or escalate."""
    if state.fatal_error:
        return "error_handler"
    if state.review_decision is ReviewDecision.APPROVED:
        return "teardown_sandbox"
    if state.review_decision is ReviewDecision.HEAL:
        return "auto_heal"
    return "error_handler"


def route_terminal(state: ReviewerState) -> str:
    """Report node → END, unless the report could not be produced."""
    if state.fatal_error or not state.review_report_markdown:
        return "error_handler"
    return "end"
