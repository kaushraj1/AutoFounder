"""ESLint + Prettier runner → list[LintResult] (plan §3.4 node 3, TS branch)."""

from __future__ import annotations

import json
import logging

from app.agents.reviewer.schema import GateStatus, LintResult
from app.agents.reviewer.tools._subprocess import binary_available
from app.agents.reviewer.tools.sandbox import Sandbox, exec_in

logger = logging.getLogger("app.agents.reviewer.tools.eslint")


async def run(sandbox: Sandbox) -> list[LintResult]:
    """Run ESLint (JSON) + Prettier (--check) over the repo. Skips if npx absent."""
    if not sandbox.container_id and not binary_available("npx"):
        logger.warning("npx not available — skipping ESLint/Prettier")
        return [
            LintResult(tool="eslint", status=GateStatus.SKIPPED),
            LintResult(tool="prettier", status=GateStatus.SKIPPED),
        ]
    return [await _eslint(sandbox), await _prettier(sandbox)]


async def _eslint(sandbox: Sandbox) -> LintResult:
    try:
        res = await exec_in(sandbox, ["npx", "eslint", ".", "-f", "json"], timeout=120.0)
    except FileNotFoundError:
        return LintResult(tool="eslint", status=GateStatus.SKIPPED)

    errors = warnings = fixable = 0
    messages: list[str] = []
    try:
        for file_report in json.loads(res.stdout or "[]"):
            errors += file_report.get("errorCount", 0)
            warnings += file_report.get("warningCount", 0)
            fixable += file_report.get("fixableErrorCount", 0) + file_report.get(
                "fixableWarningCount", 0
            )
            for m in file_report.get("messages", [])[:25]:
                messages.append(
                    f"{file_report.get('filePath', '?')}:{m.get('line', 0)} "
                    f"{m.get('ruleId', '?')} {m.get('message', '')}"
                )
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("ESLint output parse failed: %s", exc)
        return LintResult(tool="eslint", status=GateStatus.ERROR, messages=[str(exc)])

    status = GateStatus.FAILED if errors else GateStatus.PASSED
    return LintResult(
        tool="eslint",
        status=status,
        error_count=errors,
        warning_count=warnings,
        fixable_count=fixable,
        messages=messages,
    )


async def _prettier(sandbox: Sandbox) -> LintResult:
    try:
        res = await exec_in(sandbox, ["npx", "prettier", "--check", "."], timeout=90.0)
    except FileNotFoundError:
        return LintResult(tool="prettier", status=GateStatus.SKIPPED)

    if res.ok:
        return LintResult(tool="prettier", status=GateStatus.PASSED)
    # Prettier lists unformatted files on stderr; each is auto-fixable via --write.
    unformatted = [
        ln.strip()
        for ln in (res.stderr or "").splitlines()
        if ln.strip() and not ln.startswith("[")
    ]
    return LintResult(
        tool="prettier",
        status=GateStatus.FAILED,
        error_count=len(unformatted),
        fixable_count=len(unformatted),
        messages=unformatted[:25],
    )
