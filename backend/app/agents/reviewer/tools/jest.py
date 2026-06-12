"""Jest runner → TestSuiteResult (plan §3.4 node 4, TS branch).

Uses Jest's ``--json`` output for pass/fail counts and an optional
``--coverageReporters=text-summary`` line for coverage.
"""

from __future__ import annotations

import json
import logging
import re

from app.agents.reviewer.schema import GateStatus, TestFailure, TestSuiteResult
from app.agents.reviewer.tools._subprocess import binary_available
from app.agents.reviewer.tools.sandbox import Sandbox, exec_in

logger = logging.getLogger("app.agents.reviewer.tools.jest")

_COVERAGE = re.compile(r"Statements\s*:\s*(\d+(?:\.\d+)?)%")


async def run(sandbox: Sandbox) -> TestSuiteResult:
    """Run ``npx jest --json --coverage``. Skips if npx absent."""
    if not sandbox.container_id and not binary_available("npx"):
        logger.warning("npx not available — skipping Jest unit tests")
        return TestSuiteResult(runner="jest", status=GateStatus.SKIPPED)

    try:
        res = await exec_in(
            sandbox,
            ["npx", "jest", "--json", "--coverage", "--coverageReporters=text-summary"],
            timeout=180.0,
        )
    except FileNotFoundError:
        return TestSuiteResult(runner="jest", status=GateStatus.SKIPPED)

    coverage: float | None = None
    cov_match = _COVERAGE.search(f"{res.stdout}\n{res.stderr}")
    if cov_match:
        coverage = float(cov_match.group(1))

    payload = _extract_json(res.stdout)
    if payload is None:
        status = GateStatus.PASSED if res.ok else GateStatus.FAILED
        return TestSuiteResult(runner="jest", status=status, coverage_pct=coverage)

    total = int(payload.get("numTotalTests", 0))
    passed = int(payload.get("numPassedTests", 0))
    failed = int(payload.get("numFailedTests", 0))
    pending = int(payload.get("numPendingTests", 0))

    failures: list[TestFailure] = []
    for suite in payload.get("testResults", []):
        for assertion in suite.get("assertionResults", []):
            if assertion.get("status") == "failed":
                failures.append(
                    TestFailure(
                        test_id=assertion.get("fullName", assertion.get("title", "?")),
                        file_path=suite.get("name"),
                        message=" ".join(assertion.get("failureMessages", []))[:300],
                    )
                )

    status = GateStatus.PASSED if (payload.get("success") and failed == 0) else GateStatus.FAILED
    return TestSuiteResult(
        runner="jest",
        status=status,
        total=total,
        passed=passed,
        failed=failed,
        skipped=pending,
        coverage_pct=coverage,
        failures=failures,
    )


def _extract_json(stdout: str) -> dict | None:
    """Jest prints the JSON object somewhere in stdout; isolate the outer braces."""
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(stdout[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError as exc:
        logger.warning("Jest JSON parse failed: %s", exc)
        return None
