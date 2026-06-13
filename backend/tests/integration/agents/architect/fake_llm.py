"""FakeLLM — replaces call_llm() in integration tests (AF-040).

Returns pre-built, valid JSON responses for each prompt template.
The graph runs end-to-end with zero real API calls.

Usage in tests:
    from tests.integration.agents.architect.fake_llm import patch_llm

    with patch_llm():
        result = graph.invoke(initial_state)
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Pre-built responses per template (keyword-matched on prompt content)
#
# ORDERING MATTERS — first keyword match wins per call_llm() invocation:
#   • Parallel node prompts (design_erd / design_api_contract / select_stack)
#     all include requirements, which contain "FR-001". So their own unique
#     keywords must come BEFORE "FR-001".
#   • cost_forecast prompt includes scaling_plan output (contains "ecs_tasks"),
#     so "FinOps" must come BEFORE "ecs_tasks".
#   • compose_featurelist prompt includes requirements (contains "FR-001"),
#     so "canonical FeatureList" must come BEFORE "FR-001".
# ---------------------------------------------------------------------------

_RESPONSES: list[tuple[str, dict[str, Any]]] = [
    # design_erd — "erDiagram" unique to design_erd.j2
    (
        "erDiagram",
        {
            "erd_mermaid": (
                "erDiagram\n"
                "    USER {\n        uuid id PK\n        string email\n"
                "        datetime created_at\n        datetime updated_at\n    }\n"
                "    PROJECT {\n        uuid id PK\n        uuid organization_id FK\n"
                "        string name\n        datetime created_at\n"
                "        datetime updated_at\n    }\n"
                "    SECRET {\n        uuid id PK\n        uuid project_id FK\n"
                "        string key\n        datetime created_at\n"
                "        datetime updated_at\n    }\n"
                "    USER ||--o{ PROJECT : owns\n"
                "    PROJECT ||--o{ SECRET : contains"
            ),
            "entities": ["USER", "PROJECT", "SECRET"],
            "indexes": [{"table": "users", "columns": ["email"], "unique": True}],
            "design_notes": "3NF normalised",
        },
    ),
    # design_api_contract — "openapi" (lowercase) appears in .j2 JSON example
    (
        "openapi",
        {
            "openapi": "3.1.0",
            "info": {"title": "SecretSync API", "version": "1.0.0", "description": "API"},
            "servers": [{"url": "/v1"}],
            "security": [{"BearerAuth": []}],
            "paths": {
                "/projects": {
                    "get": {
                        "operationId": "list_projects",
                        "summary": "List projects",
                        "responses": {"200": {"description": "OK"}},
                    },
                    "post": {
                        "operationId": "create_project",
                        "summary": "Create project",
                        "responses": {"201": {"description": "Created"}},
                    },
                }
            },
            "components": {
                "schemas": {
                    "Project": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                        },
                    }
                },
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                },
            },
        },
    ),
    # select_stack — "Stack Selection Rules" header unique to select_stack.j2
    (
        "Stack Selection Rules",
        {
            "stack": {
                "frontend": "Next.js 14 + Tailwind CSS + shadcn/ui",
                "backend": "FastAPI (Python 3.12) + SQLAlchemy async",
                "database": "Supabase (PostgreSQL + pgvector + Auth + Realtime)",
                "cache": "Redis (AWS ElastiCache)",
                "payments": "Stripe",
                "infra": "AWS ECS Fargate + CloudFront",
            },
            "microservice_boundaries": ["auth-module", "billing-module", "secrets-module"],
            "rationale": {"backend": "FastAPI is fast and async-native"},
            "deviations_from_default": [],
        },
    ),
    # auth_strategy — "provider" unique to auth_strategy inline prompt JSON example
    (
        "provider",
        {
            "provider": "Supabase Auth",
            "mechanisms": ["email_password", "google_oauth"],
            "jwt_access_ttl_minutes": 15,
            "refresh_token_ttl_days": 30,
            "roles": [
                {"name": "owner", "permissions": ["*"]},
                {"name": "member", "permissions": ["read", "write"]},
            ],
            "api_protection": "Bearer JWT on all /v1/* endpoints",
            "service_to_service": "mTLS",
            "compliance_notes": "GDPR compliant",
        },
    ),
    # cost_forecast — "FinOps" unique to cost_forecast.j2 header.
    # Must come BEFORE "ecs_tasks": cost_forecast prompt includes scaling output.
    (
        "FinOps",
        {
            "is_estimate": True,
            "currency": "USD",
            "tiers": {
                "startup": {
                    "monthly_usd": 95.0,
                    "breakdown": {"ecs_fargate": 45.0, "supabase": 25.0, "other": 25.0},
                },
                "growth": {"monthly_usd": 320.0, "breakdown": {}},
                "scale": {"monthly_usd": 1200.0, "breakdown": {}},
            },
            "cost_surprises": ["NAT gateway egress fees"],
            "optimisations": ["Use Fargate Spot for workers"],
        },
    ),
    # compose_featurelist — "canonical FeatureList" unique to compose_featurelist.j2.
    # Must come BEFORE "FR-001": compose_featurelist prompt includes requirements.
    (
        "canonical FeatureList",
        {
            "features": [
                "Users can sign up and log in",
                "Users can create and manage projects",
                "Users can store and rotate API keys",
                "Every secret access is audited",
                "Team admins can invite members",
                "Secrets have configurable expiry dates",
                "CLI tool pulls secrets into .env files",
                "Billing managed via Stripe subscriptions",
            ],
            "integrations": ["Stripe for billing", "Supabase Auth for identity"],
            "pricing_tiers": [
                {"name": "Free", "price_usd_monthly": 0, "limits": {"projects": 1}},
                {"name": "Pro", "price_usd_monthly": 12, "limits": {"projects": 10}},
            ],
        },
    ),
    # scaling_plan — "ecs_tasks" unique to scaling_plan inline prompt JSON example.
    # Must come AFTER "FinOps": cost_forecast prompt includes scaling output.
    (
        "ecs_tasks",
        {
            "ecs_tasks": {"api": {"min": 2, "max": 10, "scale_trigger": "CPU > 70%"}},
            "db_pool": {"min_connections": 5, "max_connections": 20, "strategy": "PgBouncer"},
            "cache_strategy": {"session_ttl_seconds": 900, "what_to_cache": ["sessions"]},
            "cdn": "CloudFront for static assets",
            "rate_limiting": {
                "global_rps": 1000,
                "per_tenant_rps": 100,
                "per_endpoint_overrides": {},
            },
            "auto_scaling_notes": "Target-tracking on CPU",
        },
    ),
    # extract_requirements — "FR-001" appears in extract_requirements.j2 example JSON.
    # Must come LAST: all downstream node prompts include requirements (which have FR-001).
    (
        "FR-001",
        {
            "requirements": [
                {
                    "id": "FR-001",
                    "kind": "FR",
                    "description": "Users can sign up",
                    "priority": "P0",
                },
                {
                    "id": "FR-002",
                    "kind": "FR",
                    "description": "Users can create projects",
                    "priority": "P0",
                },
                {
                    "id": "FR-003",
                    "kind": "FR",
                    "description": "Store API keys per project",
                    "priority": "P0",
                },
                {
                    "id": "FR-004",
                    "kind": "FR",
                    "description": "Audit log every secret access",
                    "priority": "P0",
                },
                {
                    "id": "FR-005",
                    "kind": "FR",
                    "description": "Invite team members",
                    "priority": "P1",
                },
                {
                    "id": "NFR-001",
                    "kind": "NFR",
                    "description": "API p99 < 150ms",
                    "priority": "P0",
                },
                {
                    "id": "NFR-002",
                    "kind": "NFR",
                    "description": "AES-256 at rest",
                    "priority": "P0",
                },
            ],
            "use_cases": [
                {
                    "id": "UC-001",
                    "actor": "Developer",
                    "goal": "Access a secret",
                    "steps": ["login", "open project", "view secret"],
                }
            ],
        },
    ),
]


def _fake_call_llm(prompt: str, **_kwargs: Any) -> tuple[dict[str, Any], int]:
    """Match the prompt to a pre-built response by keyword lookup."""
    for keyword, response in _RESPONSES:
        if keyword in prompt:
            return response, 500
    # Fallback — return a generic non-empty dict so the graph doesn't crash
    return {"features": ["fallback feature"]}, 0


@contextmanager
def patch_llm():
    """Context manager: replace call_llm() with FakeLLM across all nodes."""
    targets = [
        "app.agents.architect.nodes.extract_requirements.call_llm",
        "app.agents.architect.nodes.design_erd.call_llm",
        "app.agents.architect.nodes.design_api_contract.call_llm",
        "app.agents.architect.nodes.select_stack.call_llm",
        "app.agents.architect.nodes.auth_strategy.call_llm",
        "app.agents.architect.nodes.scaling_plan.call_llm",
        "app.agents.architect.nodes.cost_forecast.call_llm",
        "app.agents.architect.nodes.compose_featurelist.call_llm",
    ]
    patches = [patch(t, side_effect=_fake_call_llm) for t in targets]
    for p in patches:
        p.start()
    try:
        yield
    finally:
        for p in patches:
            p.stop()
