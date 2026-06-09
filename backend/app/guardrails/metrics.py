"""Guardrail Prometheus metrics (AF-046, plan §10.5).

Declared once at import time on the default registry so ``/metrics`` (AF-024)
exposes them. Kept in a dedicated module to avoid duplicate-timeseries errors
on re-import and to keep the stage modules import-light.

Note: per-run cardinality is intentionally collapsed to the ``tenant`` label —
``run_id`` would be unbounded and is captured in the immutable lineage record,
not in metrics.
"""

from __future__ import annotations

from prometheus_client import Counter

GUARDRAIL_BLOCKS = Counter(
    "guardrail_blocks_total",
    "Calls blocked by a guardrail stage.",
    labelnames=("stage", "severity"),
)

GUARDRAIL_PII_REDACTIONS = Counter(
    "guardrail_pii_redactions_total",
    "PII spans redacted before reaching the LLM.",
    labelnames=("tenant", "kind"),
)

GUARDRAIL_INJECTION_BLOCKED = Counter(
    "guardrail_injection_blocked_total",
    "Prompt-injection attempts blocked at the input stage.",
    labelnames=("tenant",),
)

GUARDRAIL_OUTPUT_STRIKES = Counter(
    "guardrail_output_strikes_total",
    "Output-guard strikes recorded (3 -> escalate to human).",
    labelnames=("tenant",),
)

GUARDRAIL_TENANT_BREACH = Counter(
    "guardrail_tenant_breach_total",
    "SEV-1 tenant-isolation breaches detected by guardrails (must stay 0).",
)

GUARDRAIL_AUDIT_WRITE_FAILURES = Counter(
    "guardrail_audit_write_failures_total",
    "Durable audit/lineage write failures (must stay 0).",
)

GUARDRAIL_COST_CAP_BLOCKS = Counter(
    "guardrail_cost_cap_blocks_total",
    "Tool calls blocked by the execution-guard per-tenant cost cap.",
    labelnames=("tenant",),
)
