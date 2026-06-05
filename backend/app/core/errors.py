"""Error codes, domain exceptions, envelope builder, and exception handlers.

Register all handlers via ``register_exception_handlers(app)`` in ``create_app``.
Every handler returns the spec envelope:
    { "error": {code, message, details?}, "meta": {request_id, timestamp} }
Never include stack traces, SQL, or internal paths in error responses.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------


class ErrorCode(StrEnum):
    VALIDATION = "AF_ERR_VALIDATION"
    UNAUTHORIZED = "AF_ERR_UNAUTHORIZED"
    FORBIDDEN = "AF_ERR_FORBIDDEN"
    NOT_FOUND = "AF_ERR_NOT_FOUND"
    CONFLICT = "AF_ERR_CONFLICT"
    COST_CAP_EXCEEDED = "AF_ERR_COST_CAP_EXCEEDED"
    RATE_LIMITED = "AF_ERR_RATE_LIMITED"
    UNPROCESSABLE = "AF_ERR_UNPROCESSABLE"
    INTERNAL = "AF_ERR_INTERNAL"
    UNAVAILABLE = "AF_ERR_UNAVAILABLE"


_HTTP_STATUS_TO_CODE: dict[int, ErrorCode] = {
    400: ErrorCode.VALIDATION,
    401: ErrorCode.UNAUTHORIZED,
    402: ErrorCode.COST_CAP_EXCEEDED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.CONFLICT,
    422: ErrorCode.UNPROCESSABLE,
    429: ErrorCode.RATE_LIMITED,
    500: ErrorCode.INTERNAL,
    503: ErrorCode.UNAVAILABLE,
}


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class AppError(Exception):
    """Base domain error — subclass and override ``code`` + ``http_status``."""

    code: ErrorCode = ErrorCode.INTERNAL
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    code = ErrorCode.NOT_FOUND
    http_status = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    code = ErrorCode.CONFLICT
    http_status = status.HTTP_409_CONFLICT


class UnprocessableError(AppError):
    code = ErrorCode.UNPROCESSABLE
    http_status = status.HTTP_422_UNPROCESSABLE_CONTENT


class UnauthorizedError(AppError):
    code = ErrorCode.UNAUTHORIZED
    http_status = status.HTTP_401_UNAUTHORIZED


class ForbiddenError(AppError):
    code = ErrorCode.FORBIDDEN
    http_status = status.HTTP_403_FORBIDDEN


class UnavailableError(AppError):
    code = ErrorCode.UNAVAILABLE
    http_status = status.HTTP_503_SERVICE_UNAVAILABLE


# ---------------------------------------------------------------------------
# Envelope builder
# ---------------------------------------------------------------------------


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _make_error_response(
    *,
    request_id: str,
    code: ErrorCode,
    message: str,
    http_status: int,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": str(code),
            "message": message,
        },
        "meta": {
            "request_id": request_id,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }
    if details is not None:
        body["error"]["details"] = details
    resp = JSONResponse(status_code=http_status, content=body)
    # Set header directly so it's present even when middleware never runs the
    # post-response path (e.g. ServerErrorMiddleware handles the exception).
    resp.headers["X-Request-ID"] = request_id
    return resp


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return _make_error_response(
        request_id=_get_request_id(request),
        code=exc.code,
        message=exc.message,
        http_status=exc.http_status,
        details=exc.details,
    )


async def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _make_error_response(
        request_id=_get_request_id(request),
        code=ErrorCode.VALIDATION,
        message="Request validation failed.",
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
        details={"errors": exc.errors()},
    )


async def _handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = _HTTP_STATUS_TO_CODE.get(exc.status_code, ErrorCode.INTERNAL)
    message = exc.detail if isinstance(exc.detail, str) else "An error occurred."
    return _make_error_response(
        request_id=_get_request_id(request),
        code=code,
        message=message,
        http_status=exc.status_code,
    )


async def _handle_cross_tenant(request: Request, exc: Exception) -> JSONResponse:
    logger.critical("SEV-1 cross-tenant violation caught by exception handler")
    return _make_error_response(
        request_id=_get_request_id(request),
        code=ErrorCode.INTERNAL,
        message="An internal error occurred.",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def _handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return _make_error_response(
        request_id=_get_request_id(request),
        code=ErrorCode.INTERNAL,
        message="An unexpected error occurred.",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI app.

    Call once inside ``create_app`` after constructing the FastAPI instance.
    Specific exceptions must be registered before generic ones; FastAPI walks
    the MRO and uses the first matching handler.
    """
    # Deferred import avoids a circular dependency since udal imports from core.security.
    from app.db.udal import CrossTenantViolation  # noqa: PLC0415

    app.add_exception_handler(CrossTenantViolation, _handle_cross_tenant)
    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unhandled)
