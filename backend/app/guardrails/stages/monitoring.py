"""Stage 6 — Monitoring Guard (AF-046; Purnima co-owns).

Continuous drift / anomaly / abuse signals fed to LLMOps (Pillar 7). Fails
*open with alerts* — never blocks. This is the lightweight fallback for
Evidently AI: a per-agent EMA of output length plus refusal detection, enough to
surface a drift signal without the full drift-detection stack.
"""

from __future__ import annotations

import re
from typing import Any

from app.guardrails.schema import GuardrailContext, GuardrailStage, GuardResult, GuardSeverity

# EMA smoothing factor and the relative-change threshold that raises a signal.
_ALPHA = 0.2
_DRIFT_RATIO = 2.0

_REFUSAL = re.compile(
    r"(?i)\b(?:i\s+cannot|i\s+can't|i\s+am\s+unable|i'm\s+sorry,?\s+but|"
    r"as\s+an\s+ai|i\s+won't\s+be\s+able)\b"
)

# Per-agent output-length EMA baseline (reset_state() clears it).
_BASELINE: dict[str, float] = {}


def reset_state() -> None:
    """Clear the per-agent length baselines (test isolation)."""
    _BASELINE.clear()


def _text_of(output: Any) -> str:
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        return str(output.get("text") or output.get("content") or "")
    return str(output)


def observe(ctx: GuardrailContext, output: Any) -> GuardResult:
    """Record drift/refusal signals for the call. Always passes (open + alert)."""
    text = _text_of(output)
    length = float(len(text))
    flags: list[str] = []

    if _REFUSAL.search(text):
        flags.append("refusal")

    key = ctx.agent_id or ctx.organization_id
    baseline = _BASELINE.get(key)
    if baseline is not None and baseline > 0:
        ratio = length / baseline
        if ratio >= _DRIFT_RATIO or ratio <= (1.0 / _DRIFT_RATIO):
            flags.append(f"length_drift:{ratio:.2f}")
    # Update the EMA after comparing.
    _BASELINE[key] = length if baseline is None else (_ALPHA * length + (1 - _ALPHA) * baseline)

    if flags:
        return GuardResult.flag(
            GuardrailStage.monitoring,
            flags,
            reason="Monitoring signal",
            severity=GuardSeverity.INFO,
        )
    return GuardResult.ok(GuardrailStage.monitoring)
