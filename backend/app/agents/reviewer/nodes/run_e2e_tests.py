"""Node 5 — run_e2e_tests: Playwright (TS only) (plan §3.4)."""

from __future__ import annotations

from typing import Any

from app.agents.reviewer.nodes._common import to_sandbox
from app.agents.reviewer.schema import GateStatus, ReviewerState, TestSuiteResult
from app.agents.reviewer.tools import playwright
from app.agents.reviewer.utils.retry import with_retry


@with_retry("run_e2e_tests")
async def run_e2e_tests(state: ReviewerState, agent: Any) -> dict[str, Any]:
    if not state.has_typescript:
        return {"e2e_test_result": TestSuiteResult(runner="playwright", status=GateStatus.SKIPPED)}
    sandbox = to_sandbox(state)
    return {"e2e_test_result": await playwright.run(sandbox)}
