"""pytest + coverage runner → TestSuiteResult (plan §3.4 node 4, Python branch).

Parses pytest's terminal summary + ``--cov-report=term-missing`` TOTAL line from
stdout (single mockable seam, no temp-file IO).
"""

from __future__ import annotations

import logging
import re

from app.agents.reviewer.schema import GateStatus, TestFailure, TestSuiteResult
from app.agents.reviewer.tools._subprocess import binary_available
from app.agents.reviewer.tools.sandbox import Sandbox, exec_in

logger = logging.getLogger("app.agents.reviewer.tools.pytest_runner")

_PASSED = re.compile(r"(\d+) passed")
_FAILED = re.compile(r"(\d+) failed")
_SKIPPED = re.compile(r"(\d+) skipped")
_ERRORS = re.compile(r"(\d+) error")
_COVERAGE = re.compile(r"TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%")
_FAILURE_LINE = re.compile(r"FAILED\s+([^\s]+)\s*-?\s*(.*)")


async def run(sandbox: Sandbox) -> TestSuiteResult:
    """Run ``pytest -q --cov=. --cov-report=term-missing``. Skips if pytest absent."""
    if not sandbox.container_id and not binary_available("pytest"):
        logger.warning("pytest not available — skipping Python unit tests")
        return TestSuiteResult(runner="pytest", status=GateStatus.SKIPPED)

    try:
        res = await exec_in(
            sandbox,
            ["pytest", "-q", "--cov=.", "--cov-report=term-missing"],
            timeout=180.0,
        )
    except FileNotFoundError:
        return TestSuiteResult(runner="pytest", status=GateStatus.SKIPPED)

    out = f"{res.stdout}\n{res.stderr}"
    passed = _first_int(_PASSED, out)
    failed = _first_int(_FAILED, out)
    skipped = _first_int(_SKIPPED, out)
    errors = _first_int(_ERRORS, out)

    coverage: float | None = None
    cov_match = _COVERAGE.search(out)
    if cov_match:
        coverage = float(cov_match.group(1))

    failures = [
        TestFailure(test_id=m.group(1), message=m.group(2).strip()[:300])
        for m in _FAILURE_LINE.finditer(out)
    ]

    status = (
        GateStatus.PASSED
        if (res.returncode == 0 and failed == 0 and errors == 0)
        else GateStatus.FAILED
    )
    return TestSuiteResult(
        runner="pytest",
        status=status,
        total=passed + failed + skipped,
        passed=passed,
        failed=failed + errors,
        skipped=skipped,
        coverage_pct=coverage,
        failures=failures,
    )


def _first_int(pattern: re.Pattern[str], text: str) -> int:
    m = pattern.search(text)
    return int(m.group(1)) if m else 0
