"""Node 3 — run_linters: ESLint/Prettier (TS) + Ruff/Black (Py) (plan §3.4)."""

from __future__ import annotations

from typing import Any

from app.agents.reviewer.nodes._common import to_sandbox
from app.agents.reviewer.schema import LintResult, ReviewerState
from app.agents.reviewer.tools import eslint, python_lint
from app.agents.reviewer.utils.retry import with_retry


@with_retry("run_linters")
async def run_linters(state: ReviewerState, agent: Any) -> dict[str, Any]:
    sandbox = to_sandbox(state)
    results: list[LintResult] = []
    if state.has_typescript:
        results += await eslint.run(sandbox)
    if state.has_python:
        results += await python_lint.run(sandbox)
    return {"lint_results": results, "total_tool_calls": len(results)}
