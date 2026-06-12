"""Gitleaks secret scanner → list[SecurityFinding] (plan §3.4 node 6).

A committed secret is treated as a CRITICAL cryptographic-failure finding that is
NOT auto-fixable — leaked credentials must be rotated, not patched. This makes
every gitleaks hit a hard-block (escalate), which is the intended behaviour.

The report is written to a temp file (portable across Linux/Windows host-side
fallback) rather than ``/dev/stdout``. gitleaks exit codes: 0 = no leaks,
1 = leaks found, >1 = scan error — an error is NOT treated as a clean pass.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from app.agents.reviewer.schema import OWASPCategory, SecurityFinding, SeverityLevel
from app.agents.reviewer.tools._subprocess import binary_available, run_command
from app.agents.reviewer.tools.sandbox import Sandbox

logger = logging.getLogger("app.agents.reviewer.tools.gitleaks")


async def run(sandbox: Sandbox) -> list[SecurityFinding]:
    """Run ``gitleaks detect`` writing JSON to a temp report file. Skips if absent."""
    if not binary_available("gitleaks"):
        logger.warning("gitleaks not available — skipping secret scan")
        return []

    fd, report_path = tempfile.mkstemp(prefix="gitleaks-", suffix=".json")
    os.close(fd)
    try:
        res = await run_command(
            [
                "gitleaks",
                "detect",
                "--source",
                sandbox.workdir,
                "--no-git",
                "--report-format",
                "json",
                "--report-path",
                report_path,
                "--no-banner",
            ],
            timeout=60.0,
        )
        # rc 0 = clean, 1 = leaks found; anything else is a scan error (not a pass).
        if res.returncode not in (0, 1):
            logger.warning("gitleaks scan error (rc=%s): %s", res.returncode, res.stderr[:300])
            return []
        try:
            content = Path(report_path).read_text(encoding="utf-8")
        except OSError:
            return []
    finally:
        try:
            os.unlink(report_path)
        except OSError:
            pass

    if not content.strip():
        return []
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning("Gitleaks output parse failed: %s", exc)
        return []

    return [
        SecurityFinding(
            tool="gitleaks",
            severity=SeverityLevel.CRITICAL,
            rule_id=leak.get("RuleID", "secret"),
            file_path=leak.get("File", "?"),
            line=leak.get("StartLine"),
            message=f"Potential secret: {leak.get('Description', 'committed credential')}",
            owasp_category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
            cwe="CWE-798",
            auto_fixable=False,
        )
        for leak in payload
    ]
