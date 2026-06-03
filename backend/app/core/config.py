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
