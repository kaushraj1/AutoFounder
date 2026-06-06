"""Application configuration.

All environment-specific values are read here (and only here) via pydantic-settings,
validated at startup. Defaults are dev-safe so the app and tests run with no .env present;
production injects real values from AWS Secrets Manager / SSM.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-dev"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Data stores (async drivers)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres"
    redis_url: str = "redis://localhost:6379/0"

    # Supabase (Storage + Auth) — required by ObjectClient and AF-029 auth middleware
    supabase_url: str = "http://localhost:54321"
    supabase_service_key: str = "dev-service-key-change-in-prod"
    supabase_jwt_secret: str = "change-me-in-dev"

    # Authorization & OPA
    opa_url: str = "http://localhost:8181"

    # AWS & Messaging (AF-034)
    aws_region: str = "us-east-1"
    eventbridge_bus_name: str = "autofounder-platform"
    sqs_gate_decisions_queue_url: str | None = None
    sqs_pillar_queues: dict[str, str] = {}
    sqs_poll_wait_time_seconds: int = 20

    # Agent Workers
    workers_grpc_host: str = "localhost:50052"

    # Mutual TLS (mTLS) for internal service-to-service calls
    mtls_enabled: bool = False
    mtls_allowed_dns: str = "CN=orchestrator.internal,CN=workers.internal"

    # Pillar 1 — Strategy / Research (AF-037 / AF-038 / AF-039)
    gemini_api_key: str = ""
    strategy_model: str = "gemini-2.5-flash"
    tavily_api_key: str = ""
    serpapi_key: str = ""
    crunchbase_api_key: str = ""
    g2_api_key: str = ""
    similarweb_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins as a clean list, parsed from the comma-separated env value."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()
