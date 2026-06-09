"""OWASP hard-block logic (Appendix A decision D4).

Shipping a CRITICAL/HIGH injection or access-control flaw is worse than a slow
pipeline, so such findings can NEVER be auto-approved — regardless of heal cycle.
Default posture: CRITICAL/HIGH severity is *not* auto-fixable unless a scanner
explicitly proved otherwise.
"""

from __future__ import annotations

from app.agents.reviewer.schema import SecurityFinding, SeverityLevel

_BLOCKING_SEVERITIES: frozenset[SeverityLevel] = frozenset(
    {SeverityLevel.CRITICAL, SeverityLevel.HIGH}
)


def is_hard_block(finding: SecurityFinding) -> bool:
    """True if a finding must force escalation and can never be auto-approved.

    Fail-safe by SEVERITY, not by category: any un-suppressed CRITICAL/HIGH
    finding a scanner did not prove ``auto_fixable`` is a hard block — an
    unpatchable critical dependency CVE (A06) or IaC misconfig (A05) is as fatal
    to a release as an injection flaw (A03). This matches the spec fallback
    matrix: "OWASP CRITICAL/HIGH not fixable -> HARD BLOCK; never approve".
    """
    if finding.suppressed:
        return False
    if finding.severity not in _BLOCKING_SEVERITIES:
        return False
    return not finding.auto_fixable


def collect_hard_blocks(findings: list[SecurityFinding]) -> list[SecurityFinding]:
    """Return every finding that triggers an unconditional escalation."""
    return [f for f in findings if is_hard_block(f)]


def owasp_violation_labels(findings: list[SecurityFinding]) -> list[str]:
    """Stable, de-duplicated human labels for the hard-block findings."""
    labels: list[str] = []
    for f in collect_hard_blocks(findings):
        category = str(f.owasp_category) if f.owasp_category else "Unmapped-Critical"
        label = f"{category} [{f.tool}:{f.rule_id}] {f.file_path}"
        if label not in labels:
            labels.append(label)
    return labels
