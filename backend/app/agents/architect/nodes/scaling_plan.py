"""Node 5 — scaling_plan (AF-040).

Reads: requirements[] (NFRs), stack
Writes: scaling_plan{}
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.architect.llm import call_llm
from app.agents.architect.state import ArchitectState

logger = logging.getLogger(__name__)

_SCALING_PROMPT = """You are a platform engineer at AutoFounder AI.

Design the scaling plan for this application based on its NFRs and chosen stack.

## Stack
{stack}

## Non-Functional Requirements
{nfrs}

## Task
Produce a concrete scaling plan. Include:
1. Horizontal scaling targets per service (min/max ECS task counts)
2. Database connection pooling strategy
3. Caching strategy (what to cache, TTL)
4. CDN strategy for static assets
5. Rate limiting (per-tenant, per-endpoint)
6. Auto-scaling triggers (CPU %, request rate thresholds)

## Output Format
Return ONLY valid JSON:
{{
  "ecs_tasks": {{
    "api": {{"min": 2, "max": 10, "scale_trigger": "CPU > 70% for 2 min"}},
    "worker": {{"min": 1, "max": 5, "scale_trigger": "SQS queue depth > 100"}}
  }},
  "db_pool": {{
    "min_connections": 5,
    "max_connections": 20,
    "strategy": "PgBouncer transaction mode"
  }},
  "cache_strategy": {{
    "session_ttl_seconds": 900,
    "api_response_ttl_seconds": 60,
    "what_to_cache": ["user sessions", "expensive aggregation queries"]
  }},
  "cdn": "CloudFront for all /static/* and Next.js _next/static assets",
  "rate_limiting": {{
    "global_rps": 1000,
    "per_tenant_rps": 100,
    "per_endpoint_overrides": {{"/v1/auth/login": 10}}
  }},
  "auto_scaling_notes": "..."
}}
"""


def scaling_plan(state: ArchitectState) -> ArchitectState:
    """LangGraph node: design the horizontal scaling plan."""
    logger.info("[architect] scaling_plan — start")

    nfrs: list[dict[str, Any]] = [
        r for r in state.get("requirements", [])
        if r.get("kind") == "NFR"
    ]

    prompt = _SCALING_PROMPT.format(
        stack=json.dumps(state.get("stack", {}), indent=2),
        nfrs=json.dumps(nfrs, indent=2),
    )

    result, tokens = call_llm(prompt)

    logger.info("[architect] scaling_plan — done")

    return {
        **state,
        "scaling_plan": result,
        "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
    }
