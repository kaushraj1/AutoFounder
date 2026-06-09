"""Shared severity + OWASP normalisation for the security scanners.

Centralised so every scanner maps to the same ``SeverityLevel`` /
``OWASPCategory`` vocabulary — correctness here directly drives the D4 hard-block.
"""

from __future__ import annotations

from app.agents.reviewer.schema import OWASPCategory, SeverityLevel

_SEVERITY_ALIASES: dict[str, SeverityLevel] = {
    "critical": SeverityLevel.CRITICAL,
    "high": SeverityLevel.HIGH,
    "error": SeverityLevel.HIGH,
    "medium": SeverityLevel.MEDIUM,
    "moderate": SeverityLevel.MEDIUM,
    "warning": SeverityLevel.MEDIUM,
    "low": SeverityLevel.LOW,
    "info": SeverityLevel.INFO,
    "informational": SeverityLevel.INFO,
    "note": SeverityLevel.INFO,
    "unknown": SeverityLevel.LOW,
}

# Match an OWASP code (e.g. "a03") appearing anywhere in a scanner's tag string.
_OWASP_BY_CODE: dict[str, OWASPCategory] = {
    "a01": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
    "a02": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
    "a03": OWASPCategory.A03_INJECTION,
    "a04": OWASPCategory.A04_INSECURE_DESIGN,
    "a05": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
    "a06": OWASPCategory.A06_VULNERABLE_COMPONENTS,
    "a07": OWASPCategory.A07_AUTH_FAILURES,
    "a08": OWASPCategory.A08_INTEGRITY_FAILURES,
    "a09": OWASPCategory.A09_LOGGING_FAILURES,
    "a10": OWASPCategory.A10_SSRF,
}


def map_severity(raw: str | None) -> SeverityLevel:
    """Normalise any scanner's severity string to ``SeverityLevel`` (default LOW)."""
    if not raw:
        return SeverityLevel.LOW
    return _SEVERITY_ALIASES.get(raw.strip().lower(), SeverityLevel.LOW)


def map_owasp(*tags: str | None) -> OWASPCategory | None:
    """Find the first OWASP category referenced across one or more tag strings."""
    for tag in tags:
        if not tag:
            continue
        lowered = tag.lower().replace(" ", "").replace(":", "").replace("-", "")
        for code, category in _OWASP_BY_CODE.items():
            if code in lowered:
                return category
    return None
