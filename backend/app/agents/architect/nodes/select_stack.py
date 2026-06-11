"""Node 2c — select_stack (AF-040).  Runs in parallel with 2a + 2b.

Reads: requirements[], lean_canvas
Writes: stack{}, microservice_boundaries[], stack_rationale{}, stack_deviations[]
"""

from __future__ import annotations

import logging

from app.agents.architect.llm import call_llm
from app.agents.architect.prompt_loader import render
from app.agents.architect.state import ArchitectState

logger = logging.getLogger(__name__)

# Default stack to enforce unless NFRs explicitly demand deviation.
_DEFAULT_STACK = {
    "frontend": "Next.js 14 + Tailwind CSS + shadcn/ui",
    "backend": "FastAPI (Python 3.12) + SQLAlchemy async",
    "database": "Supabase (PostgreSQL + pgvector + Auth + Realtime)",
    "cache": "Redis (AWS ElastiCache)",
    "payments": "Stripe",
    "infra": "AWS ECS Fargate + CloudFront",
}


def select_stack(state: ArchitectState) -> ArchitectState:
    """LangGraph node: select tech stack and define microservice boundaries."""
    logger.info("[architect] select_stack — start")

    prompt = render(
        "select_stack",
        requirements=state.get("requirements", []),
        lean_canvas=state.get("lean_canvas", {}),
    )

    result, tokens = call_llm(prompt)

    stack: dict = result.get("stack", {})
    boundaries: list[str] = result.get("microservice_boundaries", [])
    rationale: dict = result.get("rationale", {})
    deviations: list[str] = result.get("deviations_from_default", [])

    # Enforce default stack for any keys the LLM left empty
    for key, default_value in _DEFAULT_STACK.items():
        if not stack.get(key):
            stack[key] = default_value

    logger.info(
        "[architect] select_stack — %d service boundaries, %d deviations from default",
        len(boundaries),
        len(deviations),
    )

    return {
        "stack": stack,
        "microservice_boundaries": boundaries,
        "stack_rationale": rationale,
        "stack_deviations": deviations,
        "llm_tokens_used": tokens,
    }
