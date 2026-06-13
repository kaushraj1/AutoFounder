"""Shared fixtures for Architect Agent unit tests (AF-040).

All fixtures are standalone — no real LLM, no DB, no platform.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Minimal valid data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def run_id() -> str:
    return str(uuid4())


@pytest.fixture()
def org_id() -> str:
    return "org-test-001"


@pytest.fixture()
def sample_requirements() -> list[dict[str, Any]]:
    return [
        {
            "id": "FR-001",
            "kind": "FR",
            "description": "Users can sign up with email/password",
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
            "description": "Users can store API keys per project",
            "priority": "P0",
        },
        {
            "id": "FR-004",
            "kind": "FR",
            "description": "Audit log records every secret access",
            "priority": "P0",
        },
        {
            "id": "FR-005",
            "kind": "FR",
            "description": "Team admin can invite members by email",
            "priority": "P1",
        },
        {
            "id": "NFR-001",
            "kind": "NFR",
            "description": "API p99 latency < 150 ms under 500 concurrent users",
            "priority": "P0",
        },
        {
            "id": "NFR-002",
            "kind": "NFR",
            "description": "Secrets encrypted at rest with AES-256",
            "priority": "P0",
        },
        {
            "id": "NFR-003",
            "kind": "NFR",
            "description": "99.9% monthly uptime SLA",
            "priority": "P0",
        },
        {
            "id": "NFR-004",
            "kind": "NFR",
            "description": "GDPR compliant — EU data residency option",
            "priority": "P1",
        },
    ]


@pytest.fixture()
def sample_stack() -> dict[str, str]:
    return {
        "frontend": "Next.js 14 + Tailwind CSS + shadcn/ui",
        "backend": "FastAPI (Python 3.12) + SQLAlchemy async",
        "database": "Supabase (PostgreSQL + pgvector + Auth + Realtime)",
        "cache": "Redis (AWS ElastiCache)",
        "payments": "Stripe",
        "infra": "AWS ECS Fargate + CloudFront",
    }


@pytest.fixture()
def valid_erd_mermaid() -> str:
    return """erDiagram
    USER {
        uuid id PK
        string email
        string password_hash
        string role
        datetime created_at
        datetime updated_at
    }
    PROJECT {
        uuid id PK
        uuid organization_id FK
        string name
        string description
        datetime created_at
        datetime updated_at
    }
    SECRET {
        uuid id PK
        uuid project_id FK
        string key
        string encrypted_value
        string environment
        datetime expires_at
        datetime created_at
        datetime updated_at
    }
    AUDIT_LOG {
        uuid id PK
        uuid user_id FK
        uuid secret_id FK
        string action
        string ip_address
        datetime created_at
        datetime updated_at
    }
    USER ||--o{ PROJECT : owns
    PROJECT ||--o{ SECRET : contains
    USER ||--o{ AUDIT_LOG : generates
    SECRET ||--o{ AUDIT_LOG : references"""


@pytest.fixture()
def valid_openapi_spec() -> dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "SecretSync API",
            "version": "1.0.0",
            "description": "Secrets management API",
        },
        "servers": [{"url": "/v1"}],
        "security": [{"BearerAuth": []}],
        "paths": {
            "/projects": {
                "get": {
                    "operationId": "list_projects",
                    "summary": "List all projects",
                    "responses": {"200": {"description": "Success"}},
                },
                "post": {
                    "operationId": "create_project",
                    "summary": "Create a project",
                    "responses": {"201": {"description": "Created"}},
                },
            },
            "/projects/{project_id}/secrets": {
                "get": {
                    "operationId": "list_secrets",
                    "summary": "List secrets in a project",
                    "responses": {"200": {"description": "Success"}},
                },
            },
        },
        "components": {
            "schemas": {
                "Project": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                    },
                }
            },
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            },
        },
    }


@pytest.fixture()
def valid_feature_list() -> dict[str, Any]:
    return {
        "features": [
            "Users can sign up and log in with email/password or Google SSO",
            "Users can create and manage multiple projects",
            "Users can store, read, and rotate API keys per project",
            "Every secret access is recorded in an immutable audit log",
            "Team admins can invite members by email with role assignment",
            "Secrets have configurable expiry dates with email rotation reminders",
            "CLI tool allows pulling secrets into local .env files",
            "Billing managed via Stripe with Free, Pro, and Team plans",
        ],
        "integrations": [
            "Stripe for subscription billing",
            "Supabase Auth for identity and SSO",
            "SendGrid/Resend for email notifications",
        ],
        "pricing_tiers": [
            {
                "name": "Free",
                "price_usd_monthly": 0,
                "limits": {"projects": 1, "team_members": 1},
            },
            {
                "name": "Pro",
                "price_usd_monthly": 12,
                "limits": {"projects": 10, "team_members": 5},
            },
            {
                "name": "Team",
                "price_usd_monthly": 49,
                "limits": {"projects": -1, "team_members": -1},
            },
        ],
    }


@pytest.fixture()
def full_architect_state(
    run_id: str,
    org_id: str,
    sample_requirements: list[dict],
    sample_stack: dict,
    valid_erd_mermaid: str,
    valid_openapi_spec: dict,
    valid_feature_list: dict,
) -> dict[str, Any]:
    """A fully-populated ArchitectState dict (post-graph execution)."""
    return {
        "run_id": run_id,
        "organization_id": org_id,
        "idea_normalised": "A secrets management SaaS for dev teams",
        "viability_band": "high",
        "lean_canvas": {},
        "prd": "Sample PRD text",
        "requirements": sample_requirements,
        "use_cases": [],
        "erd_mermaid": valid_erd_mermaid,
        "erd_entities": ["USER", "PROJECT", "SECRET", "AUDIT_LOG"],
        "erd_indexes": [],
        "erd_design_notes": "Normalised to 3NF",
        "openapi_3_1": valid_openapi_spec,
        "openapi_valid": True,
        "openapi_errors": [],
        "stack": sample_stack,
        "microservice_boundaries": ["auth-module", "billing-module", "secrets-module"],
        "stack_rationale": {},
        "stack_deviations": [],
        "design_complete": True,
        "auth_strategy": {"provider": "Supabase Auth", "roles": []},
        "scaling_plan": {"ecs_tasks": {}},
        "cost_estimate": {"tiers": {"startup": {"monthly_usd": 95.0}}},
        "pricing_source": "static_fallback",
        "feature_list": valid_feature_list,
        "approval_status": "approved",
        "rejection_comment": None,
        "errors": [],
        "llm_tokens_used": 1234,
    }