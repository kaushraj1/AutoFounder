"""Per-node SLA timing (plan §3.4).

``track_sla`` is an async context manager that measures wall-clock time for a
node and reports a breach (logged + Prometheus counter) WITHOUT aborting the
pipeline — an SLA breach is observability, not a hard failure.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from app.agents.reviewer import metrics

logger = logging.getLogger("app.agents.reviewer.sla")


@dataclass
class SlaProbe:
    """Carries the breach result back to the caller after the timed block exits."""

    breached: bool = False


@asynccontextmanager
async def track_sla(
    node: str,
    budget_seconds: float,
    *,
    tenant: str = "unknown",
) -> AsyncIterator[SlaProbe]:
    """Measure a node's duration and record SLA breaches.

    Always records ``reviewer_node_duration_seconds``; increments
    ``reviewer_sla_breaches_total`` and sets ``probe.breached`` if the budget is
    exceeded. Never raises on breach — the pipeline continues.
    """
    probe = SlaProbe()
    start = time.perf_counter()
    try:
        yield probe
    finally:
        elapsed = time.perf_counter() - start
        metrics.NODE_DURATION.labels(node=node, tenant=tenant, status="completed").observe(elapsed)
        if elapsed > budget_seconds:
            probe.breached = True
            metrics.SLA_BREACHES.labels(node=node).inc()
            logger.warning(
                "SLA breach: node=%s took %.2fs (budget %.2fs, tenant=%s)",
                node,
                elapsed,
                budget_seconds,
                tenant,
            )
