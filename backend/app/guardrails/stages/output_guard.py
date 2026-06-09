"""Stage 5 — Output Guard (AF-046; Purnima co-owns).

Post-generation quality checks: toxicity (lexicon fallback for Llama Guard) and
citation/groundedness (uncited factual claims). Fails *open with flags* — a hard
block hurts UX more than a warning — but tracks a per-run strike counter and
escalates to a human on the 3rd strike (CLAUDE.md §23).
"""

from __future__ import annotations

import re
from typing import Any

from app.guardrails.metrics import GUARDRAIL_OUTPUT_STRIKES
from app.guardrails.schema import GuardrailContext, GuardrailStage, GuardResult, GuardSeverity

_MAX_STRIKES = 3

# Lexicon fallback (Llama Guard substitute). Deliberately small + high-signal.
_TOXIC_TERMS = frozenset(
    {
        "kill yourself",
        "kys",
        "hate speech",
        "i hate you",
        "go die",
        "racist",
        "slur",
        "exterminate",
    }
)

# Markers suggesting a factual claim that should be grounded in a source.
_CLAIM_MARKERS = re.compile(
    r"(?i)\b(?:according to|studies show|research shows|statistics|\d+\s*%|"
    r"proven that|data shows|reportedly)\b"
)

# Per-run strike ledger (reset_state() clears it for test isolation).
_STRIKES: dict[str, int] = {}


def reset_state() -> None:
    """Clear the per-run strike ledger (test isolation)."""
    _STRIKES.clear()


def _extract(output: Any) -> tuple[str, list[Any]]:
    """Return (text, sources) from a str or a {text, sources, claims} dict."""
    if isinstance(output, str):
        return output, []
    if isinstance(output, dict):
        text = str(output.get("text") or output.get("content") or "")
        sources = output.get("sources") or output.get("citations") or []
        return text, list(sources) if isinstance(sources, list) else []
    return str(output), []


def check(ctx: GuardrailContext, output: Any) -> GuardResult:
    """Flag toxicity / uncited claims; escalate on the 3rd strike for the run."""
    text, sources = _extract(output)
    lowered = text.lower()
    flags: list[str] = []

    toxic_hits = [t for t in _TOXIC_TERMS if t in lowered]
    if toxic_hits:
        flags.append(f"toxicity:{len(toxic_hits)}")

    if _CLAIM_MARKERS.search(text) and not sources:
        flags.append("uncited_claims")

    if not flags:
        return GuardResult.ok(GuardrailStage.output, {"text": text})

    # Record a strike for this run; escalate on the 3rd.
    run_key = ctx.run_id or f"{ctx.organization_id}:{ctx.agent_id}"
    strikes = _STRIKES.get(run_key, 0) + 1
    _STRIKES[run_key] = strikes
    GUARDRAIL_OUTPUT_STRIKES.labels(tenant=ctx.organization_id).inc()

    severity = GuardSeverity.WARN
    if strikes >= _MAX_STRIKES:
        flags.append("escalate_to_human")
        severity = GuardSeverity.CRITICAL

    return GuardResult.flag(
        GuardrailStage.output,
        flags,
        reason=f"Output flagged ({', '.join(flags)}); strike {strikes}/{_MAX_STRIKES}",
        severity=severity,
        payload={"text": text},
    )
