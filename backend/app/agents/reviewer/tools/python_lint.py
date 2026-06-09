"""Ruff + Black runner → list[LintResult] (plan §3.4 node 3, Python branch)."""

from __future__ import annotations

import json
import logging

from app.agents.reviewer.schema import GateStatus, LintResult
from app.agents.reviewer.tools._subprocess import binary_available
from app.agents.reviewer.tools.sandbox import Sandbox, exec_in

logger = logging.getLogger("app.agents.reviewer.tools.python_lint")


async def run(sandbox: Sandbox) -> list[LintResult]:
    """Run Ruff (JSON) + Black (--check). Skips a tool if its binary is absent."""
    return [await _ruff(sandbox), await _black(sandbox)]


async def _ruff(sandbox: Sandbox) -> LintResult:
    if not sandbox.container_id and not binary_available("ruff"):
        return LintResult(tool="ruff", status=GateStatus.SKIPPED)
    try:
        res = await exec_in(
            sandbox, ["ruff", "check", "--output-format", "json", "."], timeout=90.0
        )
    except FileNotFoundError:
        return LintResult(tool="ruff", status=GateStatus.SKIPPED)

    messages: list[str] = []
    fixable = 0
    try:
        violations = json.loads(res.stdout or "[]")
    except json.JSONDecodeError as exc:
        logger.warning("Ruff output parse failed: %s", exc)
        return LintResult(tool="ruff", status=GateStatus.ERROR, messages=[str(exc)])

    for v in violations:
        if v.get("fix"):
            fixable += 1
        loc = v.get("location", {}) or {}
        messages.append(
            f"{v.get('filename', '?')}:{loc.get('row', 0)} "
            f"{v.get('code', '?')} {v.get('message', '')}"
        )

    errors = len(violations)
    status = GateStatus.FAILED if errors else GateStatus.PASSED
    return LintResult(
        tool="ruff",
        status=status,
        error_count=errors,
        fixable_count=fixable,
        messages=messages[:25],
    )


async def _black(sandbox: Sandbox) -> LintResult:
    if not sandbox.container_id and not binary_available("black"):
        return LintResult(tool="black", status=GateStatus.SKIPPED)
    try:
        res = await exec_in(sandbox, ["black", "--check", "."], timeout=60.0)
    except FileNotFoundError:
        return LintResult(tool="black", status=GateStatus.SKIPPED)

    if res.ok:
        return LintResult(tool="black", status=GateStatus.PASSED)
    would_reformat = [
        ln.strip()
        for ln in (res.stderr or "").splitlines()
        if ln.lower().startswith("would reformat")
    ]
    count = len(would_reformat) or 1
    return LintResult(
        tool="black",
        status=GateStatus.FAILED,
        error_count=count,
        fixable_count=count,
        messages=would_reformat[:25],
    )
