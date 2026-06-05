"""FastAPI application entry point.

Exposes a top-level ``/health`` liveness probe and the versioned ``/v1`` API. The app is
built by ``create_app`` (a factory, so tests can construct isolated instances).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIdMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks."""
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("backend.startup", env=settings.app_env, version=__version__)
    yield
    # Dispose the connection pool so the process exits cleanly.
    from app.db.session import engine  # noqa: PLC0415
    await engine.dispose()
    logger.info("backend.shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="AutoFounder AI — Backend",
        description="API gateway + LangGraph orchestrator + agent workers.",
        version=__version__,
        lifespan=lifespan,
    )

    # Middleware — add_middleware wraps in reverse: last added = outermost = runs first.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)  # outermost — stamps request_id first

    register_exception_handlers(app)

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(api_router, prefix="/v1")
    return app


app = create_app()
