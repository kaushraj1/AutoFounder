"""Prometheus metrics (AF-024).

Defines the platform metric vocabulary (CLAUDE.md §10.5 / platform plan), a timing
middleware for HTTP request latency, and a ``/metrics`` ASGI endpoint. ``prometheus_client``
is a core runtime dependency so metrics are always available.
"""

import time
from typing import TYPE_CHECKING

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

# Use the default global registry so make_asgi_app() exposes everything below.
REGISTRY: CollectorRegistry | None = None  # None => prometheus_client default registry

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "route", "status"),
)
UDAL_QUERY_DURATION = Histogram(
    "udal_query_duration_seconds",
    "UDAL data-access latency in seconds.",
    labelnames=("store", "tenant"),
)
ORCHESTRATOR_CHECKPOINT_TOTAL = Counter(
    "orchestrator_checkpoint_total",
    "LangGraph checkpoints written.",
    labelnames=("pillar",),
)
HITL_GATE_PENDING = Gauge(
    "hitl_gate_pending_total",
    "Open HITL gates awaiting a human decision.",
    labelnames=("gate_type",),
)
SQS_DLQ_MESSAGES = Counter(
    "sqs_dlq_messages_total",
    "Steps dead-lettered after exhausting retries.",
    labelnames=("queue",),
)
CROSS_TENANT_BLOCK = Counter(
    "cross_tenant_block_total",
    "SEV-1 cross-tenant isolation blocks (must stay 0).",
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Record per-request latency into ``http_request_duration_seconds``.

    The ``route`` label uses the matched route template (not the raw path) to keep
    cardinality bounded; unmatched paths collapse to ``__unmatched__``.
    """

    async def dispatch(
        self, request: "Request", call_next: "Callable[[Request], Awaitable[Response]]"
    ) -> "Response":
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        route = request.scope.get("route")
        template = getattr(route, "path", None) or "__unmatched__"
        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            route=template,
            status=str(response.status_code),
        ).observe(elapsed)
        return response


def metrics_app():  # noqa: ANN201 - returns a Starlette ASGI app
    """ASGI app serving the Prometheus exposition format (mount at /metrics)."""
    return make_asgi_app()
