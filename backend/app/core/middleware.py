"""Request-scoped middleware for the AutoFounder AI backend."""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Stamp every request with a unique, traceable ID.

    - Reads ``X-Request-ID`` from the caller (pass-through for distributed tracing).
    - Generates ``af-req-<hex>`` when absent.
    - Binds the ID to structlog contextvars so every log line in the request includes it.
    - Writes the ID to ``request.state.request_id`` for handler / service use.
    - Echoes the ID back as ``X-Request-ID`` in the response.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or f"af-req-{uuid.uuid4().hex}"
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
