"""OpenTelemetry tracing setup (AF-023).

Gated by ``settings.otel_enabled`` (default False) so dev/tests never try to export
spans, and lazily imports the OpenTelemetry SDK so the app runs without the optional
``observability`` dependency group installed. When enabled, it instruments the FastAPI
app and exports OTLP spans to ``settings.otel_exporter_otlp_endpoint`` (e.g. an
OTel Collector / AWS Distro for OpenTelemetry sidecar).
"""

from typing import TYPE_CHECKING

from app.core.config import Settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = get_logger(__name__)


def setup_tracing(app: "FastAPI", settings: Settings) -> bool:
    """Wire OpenTelemetry tracing into ``app``. Returns True if tracing was enabled.

    No-op (returns False) when ``otel_enabled`` is False or the OTel SDK is absent.
    """
    if not settings.otel_enabled:
        return False

    try:
        from opentelemetry import trace  # noqa: PLC0415
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # noqa: PLC0415
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa: PLC0415
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: PLC0415
    except ImportError:
        logger.warning("otel.disabled", reason="observability deps not installed")
        return False

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "deployment.environment": settings.app_env,
        }
    )
    provider = TracerProvider(resource=resource)
    if settings.otel_exporter_otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint))
        )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    logger.info(
        "otel.enabled",
        service=settings.otel_service_name,
        endpoint=settings.otel_exporter_otlp_endpoint,
    )
    return True
