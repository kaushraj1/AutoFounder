"""Unit — OWASP hard-block logic (D4)."""

from __future__ import annotations

from app.agents.reviewer.schema import OWASPCategory, SecurityFinding, SeverityLevel
from app.agents.reviewer.utils.owasp import (
    collect_hard_blocks,
    is_hard_block,
    owasp_violation_labels,
)


def _finding(**kw) -> SecurityFinding:
    base = dict(
        tool="semgrep",
        severity=SeverityLevel.CRITICAL,
        rule_id="sql-injection",
        file_path="app/db.py",
        message="SQL injection",
        owasp_category=OWASPCategory.A03_INJECTION,
    )
    base.update(kw)
    return SecurityFinding(**base)  # type: ignore[arg-type]


def test_critical_injection_not_fixable_is_hard_block() -> None:
    assert is_hard_block(_finding()) is True


def test_fixable_critical_is_not_hard_block() -> None:
    assert is_hard_block(_finding(auto_fixable=True)) is False


def test_suppressed_is_not_hard_block() -> None:
    assert is_hard_block(_finding(suppressed=True)) is False


def test_medium_severity_is_not_hard_block() -> None:
    assert is_hard_block(_finding(severity=SeverityLevel.MEDIUM)) is False


def test_unmapped_critical_defaults_to_block() -> None:
    assert is_hard_block(_finding(owasp_category=None)) is True


def test_vulnerable_components_high_is_hard_block() -> None:
    # Fail-safe by severity: a non-fixable HIGH dependency CVE (A06) is a hard block.
    finding = _finding(
        severity=SeverityLevel.HIGH,
        owasp_category=OWASPCategory.A06_VULNERABLE_COMPONENTS,
    )
    assert is_hard_block(finding) is True


def test_fixable_high_vulnerable_component_is_not_hard_block() -> None:
    # A dependency CVE with a fix available can heal, so it is not a hard block.
    finding = _finding(
        severity=SeverityLevel.HIGH,
        owasp_category=OWASPCategory.A06_VULNERABLE_COMPONENTS,
        auto_fixable=True,
    )
    assert is_hard_block(finding) is False


def test_collect_and_label() -> None:
    findings = [
        _finding(),
        _finding(
            severity=SeverityLevel.LOW,
            owasp_category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        ),
    ]
    blocks = collect_hard_blocks(findings)
    assert len(blocks) == 1
    labels = owasp_violation_labels(findings)
    assert len(labels) == 1
    assert "A03" in labels[0]
