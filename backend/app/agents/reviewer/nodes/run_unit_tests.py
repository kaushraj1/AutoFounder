"""Node 4 — run_unit_tests: Jest (TS) + pytest (Py), merged (plan §3.4).

Coverage gate uses the most conservative (minimum) reported coverage so a green
backend can't mask an untested frontend.
"""

from __future__ import annotations

from typing import Any

from app.agents.reviewer.nodes._common import to_sandbox
from app.agents.reviewer.schema import GateStatus, ReviewerState, TestSuiteResult
from app.agents.reviewer.tools import jest, pytest_runner
from app.agents.reviewer.utils.retry import with_retry


@with_retry("run_unit_tests")
async def run_unit_tests(state: ReviewerState, agent: Any) -> dict[str, Any]:
    sandbox = to_sandbox(state)
    results: list[TestSuiteResult] = []
    if state.has_typescript:
        results.append(await jest.run(sandbox))
    if state.has_python:
        results.append(await pytest_runner.run(sandbox))

    return {"unit_test_result": _merge(results)}


def _merge(results: list[TestSuiteResult]) -> TestSuiteResult:
    if not results:
        return TestSuiteResult(runner="none", status=GateStatus.SKIPPED)

    coverages = [r.coverage_pct for r in results if r.coverage_pct is not None]
    if any(r.status == GateStatus.FAILED for r in results):
        status = GateStatus.FAILED
    elif all(r.status == GateStatus.SKIPPED for r in results):
        status = GateStatus.SKIPPED
    else:
        status = GateStatus.PASSED

    merged = TestSuiteResult(
        runner="+".join(r.runner for r in results),
        status=status,
        total=sum(r.total for r in results),
        passed=sum(r.passed for r in results),
        failed=sum(r.failed for r in results),
        skipped=sum(r.skipped for r in results),
        coverage_pct=min(coverages) if coverages else None,
    )
    for r in results:
        merged.failures.extend(r.failures)
    return merged
