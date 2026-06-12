"""Playwright E2E runner → TestSuiteResult (plan §3.4 node 5).

Playwright's JSON reporter emits a ``stats`` object: ``expected`` (passed),
``unexpected`` (failed), ``flaky``, ``skipped``.
"""

from __future__ import annotations

import json
import logging

from app.agents.reviewer.schema import GateStatus, TestFailure, TestSuiteResult
from app.agents.reviewer.tools._subprocess import binary_available
from app.agents.reviewer.tools.sandbox import Sandbox, exec_in

logger = logging.getLogger("app.agents.reviewer.tools.playwright")


async def run(sandbox: Sandbox) -> TestSuiteResult:
    """Run ``npx playwright test --reporter=json``. Skips if npx absent.

    A Playwright failure/timeout is non-fatal: it is recorded as a FAILED gate so
    triage can decide, never crashing the pipeline (fallback matrix: skip E2E).
    """
    if not sandbox.container_id and not binary_available("npx"):
        logger.warning("npx not available — skipping Playwright E2E")
        return TestSuiteResult(runner="playwright", status=GateStatus.SKIPPED)

    try:
        res = await exec_in(
            sandbox, ["npx", "playwright", "test", "--reporter=json"], timeout=300.0
        )
    except FileNotFoundError:
        return TestSuiteResult(runner="playwright", status=GateStatus.SKIPPED)

    if res.timed_out:
        return TestSuiteResult(
            runner="playwright",
            status=GateStatus.FAILED,
            failures=[TestFailure(test_id="playwright", message="E2E run timed out")],
        )

    payload = _extract_json(res.stdout)
    if payload is None:
        status = GateStatus.PASSED if res.ok else GateStatus.FAILED
        return TestSuiteResult(runner="playwright", status=status)

    stats = payload.get("stats", {})
    passed = int(stats.get("expected", 0))
    failed = int(stats.get("unexpected", 0))
    flaky = int(stats.get("flaky", 0))
    skipped = int(stats.get("skipped", 0))

    failures: list[TestFailure] = []
    for suite in payload.get("suites", []):
        _collect_failures(suite, failures)

    status = GateStatus.PASSED if (res.returncode == 0 and failed == 0) else GateStatus.FAILED
    return TestSuiteResult(
        runner="playwright",
        status=status,
        total=passed + failed + skipped + flaky,
        passed=passed,
        failed=failed,
        skipped=skipped,
        failures=failures,
    )


def _collect_failures(suite: dict, out: list[TestFailure]) -> None:
    for spec in suite.get("specs", []):
        if not spec.get("ok", True):
            out.append(
                TestFailure(
                    test_id=spec.get("title", "?"),
                    file_path=suite.get("file"),
                    message="Playwright spec failed",
                )
            )
    for child in suite.get("suites", []):
        _collect_failures(child, out)


def _extract_json(stdout: str) -> dict | None:
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(stdout[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError as exc:
        logger.warning("Playwright JSON parse failed: %s", exc)
        return None
