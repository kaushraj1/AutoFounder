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

    # Guardrails (AF-046) — the 6-stage safety pipeline wrapping every agent call
    guardrails_enabled: bool = True
    guardrail_block_on_audit_failure: bool = False  # prod-only fail-closed on durable audit write
    guardrail_tool_cost_cap_usd: float | None = None  # default per-tenant tool spend cap (USD)
    aws_s3_audit_bucket: str = ""  # S3 Object Lock bucket for immutable lineage (7-yr)
    llama_guard_endpoint: str = ""  # optional hosted injection/safety classifier
    prompt_armor_key: str = ""  # optional injection-defense API
    posthog_key: str = ""  # optional abuse/anomaly analytics

    # AWS & Messaging (AF-034)
    aws_region: str = "us-east-1"
    eventbridge_bus_name: str = "autofounder-platform"
    sqs_gate_decisions_queue_url: str | None = None
    sqs_run_created_queue_url: str | None = None
    sqs_pillar_queues: dict[str, str] = {}
    sqs_poll_wait_time_seconds: int = 20

    # Agent Workers
    workers_grpc_host: str = "localhost:50052"

    # Mutual TLS (mTLS) for internal service-to-service calls
    mtls_enabled: bool = False
    mtls_allowed_dns: str = "CN=orchestrator.internal,CN=workers.internal"

    # LLM — Euri API (OpenAI-compatible, routes to Gemini and other models)
    euri_api_key: str = ""
    euri_base_url: str = "https://api.euron.one/api/v1/euri"
    euri_model: str = "gemini-2.5-flash"          # default model via Euri
    euri_model_pro: str = "gemini-2.5-pro"        # used for coder (larger context)

    # Legacy Gemini SDK key (not used when euri_api_key is set)
    gemini_api_key: str = ""
    strategy_model: str = "gemini-2.5-flash"
    tavily_api_key: str = ""
    serpapi_key: str = ""
    crunchbase_api_key: str = ""
    g2_api_key: str = ""
    similarweb_api_key: str = ""

    # Pillar 4 — Reviewer / Self-Healer (AF-042)
    reviewer_model: str = "gemini-2.5-flash"
    semgrep_app_token: str = ""
    snyk_token: str = ""
    sonarqube_url: str = ""
    sonarqube_token: str = ""
    sonarqube_project_key: str = ""
    github_token: str = ""
    slack_webhook_reviewer: str = ""
    aws_s3_artifacts_bucket: str = ""

    # Pillar 5 — DevOps / Deployment (AF-043)
    # TODO(AF-012-021): Replace these with terraform_remote_state lookup once Asit's
    # foundation network module ships. Until then, these are the manually-created
    # foundation VPC + subnets in ap-south-1.
    foundation_vpc_id: str = "vpc-094e84b00f220fdf5"
    foundation_private_subnet_ids: list[str] = [
        "subnet-0caeebdee8861f443",
        "subnet-0e8b9b48904794476",
    ]
    foundation_public_subnet_ids: list[str] = [
        "subnet-0cf8a83ec865e28b8",
        "subnet-017d037f8bb14a4f1",
    ]
    foundation_availability_zones: list[str] = ["ap-south-1a", "ap-south-1b"]
    foundation_aws_region: str = "ap-south-1"
    devops_spend_gate_cap_usd: float = 150.0
    # HITL spend gate — waits on Redis for founder decision when cost > cap.
    # Key is `${devops_hitl_redis_key_prefix}:{run_id}`, value 'approved'/'rejected'.
    devops_hitl_redis_key_prefix: str = "hitl:devops:spend"
    devops_hitl_poll_interval_seconds: float = 60.0
    devops_hitl_timeout_seconds: float = 900.0

    # DevOps tool execution mode. 'real' = boto3 / PyGithub / subprocess terraform.
    # 'scaffold' = canned dict returns (Phase 1A behaviour) — used by unit suites
    # that don't want to mock every AWS client.
    devops_tools_mode: str = "real"
    # Override AWS endpoint for LocalStack / motoserver / other test doubles.
    # boto3 reads AWS_ENDPOINT_URL natively, but we surface a typed field here
    # so devops tools.py can fall back to scaffold when endpoint+creds missing.
    aws_endpoint_url: str | None = None
    # Default-on safety: github_upsert_file logs the would-be commit instead of
    # pushing. Flip to False (per-run or globally) once a throwaway-org PAT is in.
    devops_github_dry_run: bool = True
    # Resolved binary used by terraform_run. Override in env to point at a
    # pinned 1.x install or a tfenv shim.
    devops_terraform_binary: str = "terraform"

    # Observability (AF-023 OTel · AF-024 Prometheus/LangSmith)
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "autofounder-backend"
    metrics_enabled: bool = True
    langsmith_api_key: str | None = None
    langsmith_project: str = "autofounder-ai"

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
