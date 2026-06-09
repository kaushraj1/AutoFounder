"""Stage 2 — Input Guard (AF-046).

Redacts PII *before* any text reaches the LLM and screens for prompt injection.
This is the regex/heuristic fallback the plan mandates when Presidio and Llama
Guard are unavailable (they are not packaged) — same degradation pattern as the
reviewer agent's scanners. Fails *closed* on a high-confidence injection.
"""

from __future__ import annotations

import re
from typing import Any

from app.guardrails.metrics import GUARDRAIL_INJECTION_BLOCKED, GUARDRAIL_PII_REDACTIONS
from app.guardrails.schema import GuardrailContext, GuardrailStage, GuardResult, GuardSeverity

# --- PII patterns (priority order: most specific first) --------------------

_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws_key", re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA)[0-9A-Z]{16}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("phone", re.compile(r"\b(?:\+?\d{1,2}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b")),
]

_CREDIT_CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")

# --- Injection heuristics --------------------------------------------------

_INJECTION_HIGH: list[re.Pattern[str]] = [
    re.compile(
        r"ignore\s+(?:all\s+|the\s+|any\s+)?(?:(?:previous|prior|above|system)\s+){1,3}"
        r"(?:instructions?|prompts?|messages?|context)",
        re.I,
    ),
    re.compile(r"disregard\s+(?:all\s+|the\s+|your\s+)?(?:previous|prior|above|system)", re.I),
    re.compile(r"forget\s+(?:all|everything|your)\s+(?:previous|instructions?|above)", re.I),
    re.compile(
        r"(?:reveal|print|show|repeat|output)\s+(?:your\s+)?(?:system\s+)?"
        r"(?:prompt|instructions?)",
        re.I,
    ),
    re.compile(r"\bdo\s+anything\s+now\b", re.I),
    re.compile(r"developer\s+mode", re.I),
    re.compile(r"override\s+(?:your\s+)?(?:safety|guard(?:rail)?s?|instructions?)", re.I),
    re.compile(r"you\s+are\s+(?:now\s+)?(?:in\s+)?(?:jailbreak|dan|unrestricted)", re.I),
]

_INJECTION_MEDIUM: list[re.Pattern[str]] = [
    re.compile(r"system\s+prompt", re.I),
    re.compile(r"you\s+are\s+now\b", re.I),
    re.compile(r"pretend\s+(?:to\s+be|you\s+are)", re.I),
    re.compile(r"\bbypass\b", re.I),
    re.compile(r"\bexfiltrate\b", re.I),
    re.compile(r"new\s+instructions\s*:", re.I),
]

_SCAN_KEYS = ("prompt", "input", "text", "system_prompt", "query", "content", "instruction")


def _luhn_ok(number: str) -> bool:
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _redact_text(text: str, counts: dict[str, int]) -> str:
    # Credit cards first (Luhn-validated to avoid false positives).
    def _cc_sub(m: re.Match[str]) -> str:
        if _luhn_ok(m.group()):
            counts["credit_card"] = counts.get("credit_card", 0) + 1
            return "[REDACTED_CREDIT_CARD]"
        return m.group()

    text = _CREDIT_CARD.sub(_cc_sub, text)

    for kind, pattern in _PII_PATTERNS:

        def _sub(m: re.Match[str], _kind: str = kind) -> str:
            counts[_kind] = counts.get(_kind, 0) + 1
            return f"[REDACTED_{_kind.upper()}]"

        text = pattern.sub(_sub, text)
    return text


def _redact_obj(obj: Any, counts: dict[str, int]) -> Any:
    if isinstance(obj, str):
        return _redact_text(obj, counts)
    if isinstance(obj, dict):
        return {k: _redact_obj(v, counts) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_obj(v, counts) for v in obj]
    return obj


def _collect_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in _SCAN_KEYS:
        val = payload.get(key)
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, dict | list):
            parts.append(str(val))
    return "\n".join(parts) if parts else str(payload)


def check(ctx: GuardrailContext, payload: dict[str, Any]) -> GuardResult:
    """Redact PII and screen for injection. Block on high-confidence injection."""
    text = _collect_text(payload)

    # --- Injection screen (fail closed) ---
    if any(p.search(text) for p in _INJECTION_HIGH):
        GUARDRAIL_INJECTION_BLOCKED.labels(tenant=ctx.organization_id).inc()
        return GuardResult.block(
            GuardrailStage.input,
            "Prompt injection detected (high-confidence pattern)",
            severity=GuardSeverity.CRITICAL,
            flags=["injection:high"],
        )
    medium_hits = sum(1 for p in _INJECTION_MEDIUM if p.search(text))
    if medium_hits >= 2:
        GUARDRAIL_INJECTION_BLOCKED.labels(tenant=ctx.organization_id).inc()
        return GuardResult.block(
            GuardrailStage.input,
            "Prompt injection detected (multiple suspicious patterns)",
            severity=GuardSeverity.CRITICAL,
            flags=["injection:medium"],
        )

    # --- PII redaction (sanitize, do not block) ---
    counts: dict[str, int] = {}
    sanitized = _redact_obj(payload, counts)
    flags: list[str] = []
    for kind, n in counts.items():
        GUARDRAIL_PII_REDACTIONS.labels(tenant=ctx.organization_id, kind=kind).inc(n)
        flags.append(f"pii:{kind}={n}")
    if medium_hits == 1:
        flags.append("injection:suspicious")

    if flags:
        result = GuardResult.flag(
            GuardrailStage.input,
            flags,
            reason="PII redacted / suspicious input flagged",
            severity=GuardSeverity.WARN,
            payload=sanitized,
        )
        return result
    return GuardResult.ok(GuardrailStage.input, sanitized)
