"""Structured (JSON) logging via structlog.

Every log line is a single JSON object so CloudWatch / ELK can index it. Call
``configure_logging`` once at startup; use ``get_logger(__name__)`` everywhere else.
"""

import logging
from collections.abc import MutableMapping
from typing import Any

import structlog

EventDict = MutableMapping[str, Any]

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
}


def _env_processor(env: str) -> Any:
    """Stamp every log line with the deployment environment (AF-023 mandatory field)."""

    def processor(_logger: Any, _method: str, event_dict: EventDict) -> EventDict:
        event_dict.setdefault("env", env)
        return event_dict

    return processor


def _otel_trace_processor(_logger: Any, _method: str, event_dict: EventDict) -> EventDict:
    """Inject the active OpenTelemetry trace_id/span_id when a span is in scope.

    Best-effort: a no-op if OTel is not installed or no span is active, so logging
    never depends on the optional observability extra.
    """
    try:
        from opentelemetry import trace  # noqa: PLC0415

        ctx = trace.get_current_span().get_span_context()
        if ctx is not None and ctx.is_valid:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    except Exception:  # noqa: BLE001 - tracing context is best-effort, never fatal
        pass
    return event_dict


def configure_logging(level: str = "INFO", env: str = "development") -> None:
    """Configure stdlib logging + structlog for JSON output at the given level.

    The mandatory AF-023 fields are emitted as follows: ``env`` and ``trace_id`` are
    injected here; ``request_id`` by ``RequestIdMiddleware``; and ``organization_id``,
    ``run_id``, ``agent_id``, ``model`` are merged from contextvars when the request /
    orchestrator / agent layers bind them via :func:`bind_log_context`.
    """
    log_level = _LEVELS.get(level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", level=log_level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _env_processor(env),
            _otel_trace_processor,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def bind_log_context(**fields: Any) -> None:
    """Bind mandatory trace fields (organization_id, run_id, agent_id, model, ...) into
    the structlog context so every subsequent log line in this context carries them."""
    structlog.contextvars.bind_contextvars(**fields)


def get_logger(name: str | None = None) -> Any:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
