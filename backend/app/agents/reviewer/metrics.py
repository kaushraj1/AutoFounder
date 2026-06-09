"""Reviewer Prometheus metrics (plan §10.5).

Defined once at import time on the default registry so ``/metrics`` (AF-024)
exposes them. Kept in a dedicated module to avoid duplicate-timeseries errors
on re-import and to keep nodes import-light.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

NODE_DURATION = Histogram(
    "reviewer_node_duration_seconds",
    "Per-node wall-clock duration of the Reviewer graph.",
    labelnames=("node", "tenant", "status"),
)

HEAL_CYCLES = Histogram(
    "reviewer_heal_cycles_total",
    "Self-heal cycles used per run.",
    labelnames=("tenant", "decision"),
    buckets=(0, 1, 2, 3, 4, 5),
)

AUTOFIX_RATE = Gauge(
    "reviewer_autofix_rate",
    "Fraction of fixable issues actually fixed (target >= 0.90).",
    labelnames=("tenant",),
)

SECURITY_FINDINGS = Counter(
    "reviewer_security_findings_total",
    "Security findings discovered.",
    labelnames=("severity", "tool", "owasp"),
)

OWASP_BLOCKS = Counter(
    "reviewer_owasp_blocks_total",
    "Hard-block escalations forced by CRITICAL/HIGH OWASP findings.",
    labelnames=("owasp",),
)

DECISION = Counter(
    "reviewer_decision_total",
    "Verdict distribution (approved / heal / escalate).",
    labelnames=("decision",),
)

SLA_BREACHES = Counter(
    "reviewer_sla_breaches_total",
    "Per-node SLA breaches (non-fatal).",
    labelnames=("node",),
)

HIGH_HEAL_CYCLES = Counter(
    "reviewer_high_heal_cycles_total",
    "Runs that needed >= 4 heal cycles (flagged for Coder-prompt review).",
    labelnames=("tenant",),
)
