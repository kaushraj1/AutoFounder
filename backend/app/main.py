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
from app.core.metrics import PrometheusMiddleware, metrics_app
from app.core.middleware import RequestIdMiddleware
from app.core.observability import setup_tracing

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks."""
    import asyncio  # noqa: PLC0415

    settings = get_settings()
    configure_logging(settings.log_level, env=settings.app_env)
    logger.info("backend.startup", env=settings.app_env, version=__version__)
    from app.db.redis_pool import get_redis, init_redis  # noqa: PLC0415
    from app.db.session import SessionLocal  # noqa: PLC0415
    from app.orchestrator import OrchestratorEngine  # noqa: PLC0415
    from app.orchestrator.events.consumer import SQSGateDecisionConsumer, SQSRunCreatedConsumer  # noqa: PLC0415
    from app.orchestrator.worker import SQSPillarWorker  # noqa: PLC0415

    await init_redis()

    engine_inst = OrchestratorEngine(session_factory=SessionLocal, redis=get_redis())
    consumer = SQSGateDecisionConsumer(engine=engine_inst)
    run_created_consumer = SQSRunCreatedConsumer(engine=engine_inst)
    worker = SQSPillarWorker(engine=engine_inst, redis=get_redis())

    consumer_task = asyncio.create_task(consumer.start())
    run_created_task = asyncio.create_task(run_created_consumer.start())
    worker_task = asyncio.create_task(worker.start())

    yield

    consumer_task.cancel()
    run_created_task.cancel()
    worker_task.cancel()
    await asyncio.gather(consumer_task, run_created_task, worker_task, return_exceptions=True)

    from app.db.redis_pool import close_redis  # noqa: PLC0415
    from app.db.session import engine  # noqa: PLC0415

    await engine.dispose()
    await close_redis()
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
    if settings.metrics_enabled:
        app.add_middleware(PrometheusMiddleware)  # times every request
    app.add_middleware(RequestIdMiddleware)  # outermost — stamps request_id first

    register_exception_handlers(app)

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(api_router, prefix="/v1")

    # Observability (AF-024 Prometheus /metrics · AF-023 OTel tracing, gated).
    if settings.metrics_enabled:
        app.mount("/metrics", metrics_app())
    setup_tracing(app, settings)

    return app


app = create_app()
