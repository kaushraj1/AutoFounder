"""Unit — conditional-edge routers."""

from __future__ import annotations

from tests.agents.reviewer.conftest import make_state

from app.agents.reviewer.routers import (
    PARALLEL_GATES,
    route_after_ingest,
    route_after_join,
    route_after_judge,
    route_after_sandbox,
    route_after_triage,
    route_terminal,
)
from app.agents.reviewer.schema import GateStatus, ReviewDecision, TestSuiteResult


def test_route_after_ingest() -> None:
    assert route_after_ingest(make_state()) == "spin_sandbox"
    assert route_after_ingest(make_state(fatal_error="boom")) == "error_handler"


def test_route_after_sandbox_fans_out() -> None:
    assert route_after_sandbox(make_state()) == PARALLEL_GATES
    assert route_after_sandbox(make_state(fatal_error="boom")) == ["error_handler"]


def test_route_after_join() -> None:
    ok = make_state(unit_test_result=TestSuiteResult(runner="pytest", status=GateStatus.PASSED))
    assert route_after_join(ok) == "llm_judge"
    assert route_after_join(make_state(fatal_error="x")) == "error_handler"
    # Unit gate crashed (no result + recorded fault) → escalate, don't judge blind.
    crashed = make_state(unit_test_result=None, error_count=1)
    assert route_after_join(crashed) == "error_handler"


def test_route_after_judge() -> None:
    assert route_after_judge(make_state()) == "triage_failures"
    assert route_after_judge(make_state(fatal_error="x")) == "error_handler"


def test_route_after_triage() -> None:
    approved = make_state(review_decision=ReviewDecision.APPROVED)
    heal = make_state(review_decision=ReviewDecision.HEAL)
    escalate = make_state(review_decision=ReviewDecision.ESCALATE)
    assert route_after_triage(approved) == "teardown_sandbox"
    assert route_after_triage(heal) == "auto_heal"
    assert route_after_triage(escalate) == "error_handler"
    assert route_after_triage(make_state(fatal_error="x")) == "error_handler"


def test_route_terminal() -> None:
    with_report = make_state(review_report_markdown="# r")
    fatal = make_state(review_report_markdown="# r", fatal_error="x")
    assert route_terminal(with_report) == "end"
    assert route_terminal(make_state()) == "error_handler"
    assert route_terminal(fatal) == "error_handler"
