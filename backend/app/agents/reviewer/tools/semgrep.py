"""Semgrep SAST scanner → list[SecurityFinding] (plan §3.4 node 6).

Prefers the cloud OWASP ruleset when ``app_token`` is set; falls back to the
local ``p/owasp-top-ten`` config (fallback matrix: Semgrep API down → local CLI).
"""

from __future__ import annotations

import json
import logging

from app.agents.reviewer.schema import SecurityFinding
from app.agents.reviewer.tools._findings import map_owasp, map_severity
from app.agents.reviewer.tools._subprocess import binary_available, run_command
from app.agents.reviewer.tools.sandbox import Sandbox

logger = logging.getLogger("app.agents.reviewer.tools.semgrep")


async def run(sandbox: Sandbox, *, app_token: str | None = None) -> list[SecurityFinding]:
    """Run ``semgrep --json --config p/owasp-top-ten``. Skips if semgrep absent."""
    if not binary_available("semgrep"):
        logger.warning("semgrep not available — skipping SAST scan")
        return []

    env = {"SEMGREP_APP_TOKEN": app_token} if app_token else None
    res = await run_command(
        ["semgrep", "--json", "--quiet", "--config", "p/owasp-top-ten", sandbox.workdir],
        timeout=120.0,
        env=env,
    )
    if not res.stdout.strip():
        return []

    try:
        payload = json.loads(res.stdout)
    except json.JSONDecodeError as exc:
        logger.warning("Semgrep output parse failed: %s", exc)
        return []

    findings: list[SecurityFinding] = []
    for r in payload.get("results", []):
        extra = r.get("extra", {}) or {}
        metadata = extra.get("metadata", {}) or {}
        owasp_tags = metadata.get("owasp")
        if isinstance(owasp_tags, list):
            owasp_str = " ".join(str(t) for t in owasp_tags)
        else:
            owasp_str = str(owasp_tags or "")
        cwe_str = _first_cwe(metadata.get("cwe"))
        findings.append(
            SecurityFinding(
                tool="semgrep",
                severity=map_severity(extra.get("severity")),
                rule_id=r.get("check_id", "semgrep-rule"),
                file_path=r.get("path", "?"),
                line=(r.get("start", {}) or {}).get("line"),
                message=extra.get("message", "")[:500],
                owasp_category=map_owasp(owasp_str, r.get("check_id")),
                cwe=cwe_str,
            )
        )
    return findings


def _first_cwe(cwe: object) -> str | None:
    """Semgrep reports cwe as a list or a string depending on the rule."""
    if isinstance(cwe, list) and cwe:
        return str(cwe[0])
    if isinstance(cwe, str):
        return cwe
    return None
