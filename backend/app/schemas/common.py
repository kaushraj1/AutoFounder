"""Shared response schemas — envelopes, pagination, and metadata used across all endpoints."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class HealthResponse(BaseModel):
    """Liveness probe payload."""

    status: str
    service: str
    version: str
    env: str


class ErrorDetail(BaseModel):
    """Inner error object — code, human-readable message, optional machine detail."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class Meta(BaseModel):
    """Request metadata attached to every response."""

    request_id: str
    timestamp: datetime


class ErrorEnvelope(BaseModel):
    """Spec-compliant error envelope returned by all exception handlers."""

    error: ErrorDetail
    meta: Meta


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard success response wrapper."""

    data: T
    meta: Meta


class PaginationInfo(BaseModel):
    """Opaque cursor-based pagination details."""

    cursor: str | None = None
    has_more: bool = False
    total: int


class PaginatedResponseEnvelope(BaseModel, Generic[T]):
    """Paginated collection success response wrapper."""

    data: list[T]
    pagination: PaginationInfo
    meta: Meta
