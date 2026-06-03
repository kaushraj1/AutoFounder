"""Liveness/health endpoint."""

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Return service status — used by the load balancer and container health check."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="autofounder-ai-backend",
        version=__version__,
        env=settings.app_env,
    )
