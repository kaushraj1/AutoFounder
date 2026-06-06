"""AF-024 — Prometheus metrics wiring tests (no app lifespan / external deps)."""

from app.core import metrics
from app.main import create_app


def test_metrics_endpoint_mounted() -> None:
    """The /metrics endpoint is mounted when metrics are enabled (default)."""
    app = create_app()
    paths = [getattr(route, "path", None) for route in app.routes]
    assert "/metrics" in paths


def test_metric_vocabulary_defined() -> None:
    """The platform metric vocabulary (plan §10.5) is registered and scrapeable."""
    from prometheus_client import generate_latest

    # Touch a couple so they appear in the exposition output.
    metrics.ORCHESTRATOR_CHECKPOINT_TOTAL.labels(pillar="1").inc()
    metrics.CROSS_TENANT_BLOCK.inc(0)

    exposition = generate_latest().decode()
    assert "http_request_duration_seconds" in exposition
    assert "cross_tenant_block_total" in exposition
    assert "orchestrator_checkpoint_total" in exposition
