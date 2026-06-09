"""Node 6 — run_security_scan: Trivy + Semgrep + Bandit + Snyk + Gitleaks (plan §3.4).

Aggregates all scanners into ``security_findings`` and records per-finding metrics.
Each scanner degrades to an empty list when its binary/token is missing, so the
gate is best-effort and never crashes the pipeline.
"""

from __future__ import annotations

from typing import Any

from app.agents.reviewer import metrics
from app.agents.reviewer.nodes._common import to_sandbox
from app.agents.reviewer.schema import ReviewerState, SecurityFinding
from app.agents.reviewer.tools import bandit, gitleaks, semgrep, snyk, trivy
from app.agents.reviewer.utils.retry import with_retry
from app.core.config import get_settings


@with_retry("run_security_scan")
async def run_security_scan(state: ReviewerState, agent: Any) -> dict[str, Any]:
    settings = get_settings()
    sandbox = to_sandbox(state)
    findings: list[SecurityFinding] = []

    findings += await trivy.run(sandbox)
    findings += await semgrep.run(sandbox, app_token=settings.semgrep_app_token or None)
    findings += await gitleaks.run(sandbox)
    if state.has_python:
        findings += await bandit.run(sandbox)
    if settings.snyk_token:
        findings += await snyk.run(sandbox, token=settings.snyk_token)

    for f in findings:
        owasp = str(f.owasp_category) if f.owasp_category else "none"
        metrics.SECURITY_FINDINGS.labels(severity=str(f.severity), tool=f.tool, owasp=owasp).inc()

    return {"security_findings": findings, "total_tool_calls": 5}
