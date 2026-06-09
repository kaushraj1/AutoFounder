"""Trivy CVE + IaC scanner → list[SecurityFinding] (plan §3.4 node 6).

Trivy filesystem scan covers vulnerable dependencies (OWASP A06) and IaC
misconfigurations (A05). Runs host-side against the cloned repo; non-fatal when
the binary is absent.
"""

from __future__ import annotations

import json
import logging

from app.agents.reviewer.schema import OWASPCategory, SecurityFinding
from app.agents.reviewer.tools._findings import map_severity
from app.agents.reviewer.tools._subprocess import binary_available, run_command
from app.agents.reviewer.tools.sandbox import Sandbox

logger = logging.getLogger("app.agents.reviewer.tools.trivy")


async def run(sandbox: Sandbox) -> list[SecurityFinding]:
    """Run ``trivy fs --format json`` over the workdir. Skips if trivy absent."""
    if not binary_available("trivy"):
        logger.warning("trivy not available — skipping CVE/IaC scan")
        return []

    res = await run_command(
        ["trivy", "fs", "--quiet", "--format", "json", sandbox.workdir],
        timeout=120.0,
    )
    if not res.stdout.strip():
        return []

    try:
        payload = json.loads(res.stdout)
    except json.JSONDecodeError as exc:
        logger.warning("Trivy output parse failed: %s", exc)
        return []

    findings: list[SecurityFinding] = []
    for result in payload.get("Results", []):
        target = result.get("Target", "?")
        for vuln in result.get("Vulnerabilities", []) or []:
            cwes = vuln.get("CweIDs") or []
            findings.append(
                SecurityFinding(
                    tool="trivy",
                    severity=map_severity(vuln.get("Severity")),
                    rule_id=vuln.get("VulnerabilityID", "CVE-UNKNOWN"),
                    file_path=target,
                    message=f"{vuln.get('PkgName', '?')}: {vuln.get('Title', '')}".strip(),
                    owasp_category=OWASPCategory.A06_VULNERABLE_COMPONENTS,
                    cwe=cwes[0] if cwes else None,
                    auto_fixable=bool(vuln.get("FixedVersion")),
                )
            )
        for misc in result.get("Misconfigurations", []) or []:
            findings.append(
                SecurityFinding(
                    tool="trivy",
                    severity=map_severity(misc.get("Severity")),
                    rule_id=misc.get("ID", "AVD-UNKNOWN"),
                    file_path=target,
                    message=misc.get("Title", "IaC misconfiguration"),
                    owasp_category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
                )
            )
    return findings
