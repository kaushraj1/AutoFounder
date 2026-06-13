"""Node 4 — auth_strategy (AF-040).

Reads: requirements[], stack
Writes: auth_strategy{}
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.architect.llm import call_llm
from app.agents.architect.state import ArchitectState

logger = logging.getLogger(__name__)

_AUTH_PROMPT = """You are a security architect at AutoFounder AI.

Design the authentication and authorisation strategy for this application.

## Stack
{stack}

## Non-Functional Requirements (security-related)
{nfrs}

## Task
Design a complete auth strategy. Include:
1. Authentication mechanism (e.g. Supabase Auth with email/password + OAuth providers)
2. Session management (JWT access token TTL, refresh token strategy)
3. RBAC model: list all roles and their permissions
4. API security: how every REST endpoint is protected
5. Service-to-service auth (internal calls)
6. Any compliance considerations (GDPR, HIPAA-adjacent, SOC2)

## Output Format
Return ONLY valid JSON:
{{
  "provider": "Supabase Auth",
  "mechanisms": ["email_password", "google_oauth", "github_oauth"],
  "jwt_access_ttl_minutes": 15,
  "refresh_token_ttl_days": 30,
  "roles": [
    {{"name": "owner", "permissions": ["*"]}},
    {{"name": "admin", "permissions": ["read", "write", "invite"]}},
    {{"name": "member", "permissions": ["read", "write"]}},
    {{"name": "viewer", "permissions": ["read"]}}
  ],
  "api_protection": "Bearer JWT on all /v1/* endpoints via FastAPI dependency",
  "service_to_service": "mTLS with short-lived JWT signed by internal CA",
  "compliance_notes": "..."
}}
"""


def auth_strategy(state: ArchitectState) -> ArchitectState:
    """LangGraph node: design the auth and RBAC strategy."""
    logger.info("[architect] auth_strategy — start")

    nfrs: list[dict[str, Any]] = [
        r for r in state.get("requirements", []) if r.get("kind") == "NFR"
    ]

    import json

    prompt = _AUTH_PROMPT.format(
        stack=json.dumps(state.get("stack", {}), indent=2),
        nfrs=json.dumps(nfrs, indent=2),
    )

    result, tokens = call_llm(prompt)

    logger.info(
        "[architect] auth_strategy — provider=%s, %d roles",
        result.get("provider", "unknown"),
        len(result.get("roles", [])),
    )

    return {
        "auth_strategy": result,
        "llm_tokens_used": tokens,
    }
