"""Shared response schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness probe payload."""

    status: str
    service: str
    version: str
    env: str


class ErrorResponse(BaseModel):
    """Consistent error envelope used across all endpoints (see CLAUDE.md §85)."""

    error: str
    code: str
    message: str
    details: dict[str, object] | None = None
