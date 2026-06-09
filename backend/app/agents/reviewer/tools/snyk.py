"""Snyk dependency-vulnerability scanner → list[SecurityFinding] (plan §3.4 node 6).

Requires ``SNYK_TOKEN``; absent token or binary → non-fatal skip (fallback matrix).
"""

from __future__ import annotations

import json
import logging

from app.agents.reviewer.schema import OWASPCategory, SecurityFinding
from app.agents.reviewer.tools._findings import map_severity
from app.agents.reviewer.tools._subprocess import binary_available, run_command
from app.agents.reviewer.tools.sandbox import Sandbox

logger = logging.getLogger("app.agents.reviewer.tools.snyk")


async def run(sandbox: Sandbox, *, token: str | None = None) -> list[SecurityFinding]:
    """Run ``snyk test --json``. Skips if snyk binary or token is missing."""
    if not binary_available("snyk"):
        logger.warning("snyk not available — skipping dependency scan")
        return []
    if not token:
        logger.warning("SNYK_TOKEN not configured — skipping dependency scan")
        return []

    res = await run_command(
        ["snyk", "test", "--json"],
        cwd=sandbox.workdir,
        timeout=90.0,
        env={"SNYK_TOKEN": token},
    )
    if not res.stdout.strip():
        return []

    try:
        payload = json.loads(res.stdout)
    except json.JSONDecodeError as exc:
        logger.warning("Snyk output parse failed: %s", exc)
        return []

    # Snyk emits a dict for a single project, or a list for multiple manifests.
    projects = payload if isinstance(payload, list) else [payload]
    findings: list[SecurityFinding] = []
    for project in projects:
        target = project.get("displayTargetFile", "dependencies")
        for vuln in project.get("vulnerabilities", []) or []:
            cwes = (vuln.get("identifiers", {}) or {}).get("CWE") or []
            findings.append(
                SecurityFinding(
                    tool="snyk",
                    severity=map_severity(vuln.get("severity")),
                    rule_id=vuln.get("id", "SNYK-UNKNOWN"),
                    file_path=target,
                    message=f"{vuln.get('packageName', '?')}: {vuln.get('title', '')}".strip(),
                    owasp_category=OWASPCategory.A06_VULNERABLE_COMPONENTS,
                    cwe=cwes[0] if cwes else None,
                    auto_fixable=bool(vuln.get("fixedIn") or vuln.get("isUpgradable")),
                )
            )
    return findings
