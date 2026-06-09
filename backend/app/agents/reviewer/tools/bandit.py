"""Bandit Python security scanner → list[SecurityFinding] (plan §3.4 node 6).

Python-only; the node only calls this when the repo has Python sources.
"""

from __future__ import annotations

import json
import logging

from app.agents.reviewer.schema import OWASPCategory, SecurityFinding
from app.agents.reviewer.tools._findings import map_severity
from app.agents.reviewer.tools._subprocess import binary_available, run_command
from app.agents.reviewer.tools.sandbox import Sandbox

logger = logging.getLogger("app.agents.reviewer.tools.bandit")

# Common Bandit test IDs → OWASP category (best-effort; default None).
_BANDIT_OWASP: dict[str, OWASPCategory] = {
    "B608": OWASPCategory.A03_INJECTION,  # hardcoded SQL expression
    "B602": OWASPCategory.A03_INJECTION,  # subprocess shell=True
    "B605": OWASPCategory.A03_INJECTION,  # start process with a shell
    "B105": OWASPCategory.A07_AUTH_FAILURES,  # hardcoded password string
    "B106": OWASPCategory.A07_AUTH_FAILURES,  # hardcoded password funcarg
    "B107": OWASPCategory.A07_AUTH_FAILURES,  # hardcoded password default
    "B303": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # weak MD5/SHA1
    "B501": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # request without cert validation
    "B201": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # flask debug=True
}


async def run(sandbox: Sandbox) -> list[SecurityFinding]:
    """Run ``bandit -r -f json``. Skips if bandit absent."""
    if not binary_available("bandit"):
        logger.warning("bandit not available — skipping Python security scan")
        return []

    res = await run_command(
        ["bandit", "-r", "-q", "-f", "json", sandbox.workdir],
        timeout=90.0,
    )
    if not res.stdout.strip():
        return []

    try:
        payload = json.loads(res.stdout)
    except json.JSONDecodeError as exc:
        logger.warning("Bandit output parse failed: %s", exc)
        return []

    findings: list[SecurityFinding] = []
    for r in payload.get("results", []):
        test_id = r.get("test_id", "B000")
        cwe = (r.get("issue_cwe") or {}).get("id")
        findings.append(
            SecurityFinding(
                tool="bandit",
                severity=map_severity(r.get("issue_severity")),
                rule_id=test_id,
                file_path=r.get("filename", "?"),
                line=r.get("line_number"),
                message=r.get("issue_text", "")[:500],
                owasp_category=_BANDIT_OWASP.get(test_id),
                cwe=f"CWE-{cwe}" if cwe else None,
            )
        )
    return findings
