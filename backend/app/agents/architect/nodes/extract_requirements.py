"""Node 1 — extract_requirements (AF-040).

Reads: prd, lean_canvas, idea_normalised, viability_band
Writes: requirements[], use_cases[]
"""

from __future__ import annotations

import logging

from app.agents.architect.llm import call_llm
from app.agents.architect.prompt_loader import render
from app.agents.architect.state import ArchitectState

logger = logging.getLogger(__name__)


def extract_requirements(state: ArchitectState) -> ArchitectState:
    """LangGraph node: extract FRs, NFRs, and use cases from the PRD."""
    logger.info("[architect] extract_requirements — start")

    prompt = render(
        "extract_requirements",
        idea_normalised=state.get("idea_normalised", ""),
        lean_canvas=state.get("lean_canvas", {}),
        prd=state.get("prd", ""),
        viability_band=state.get("viability_band", "unknown"),
    )

    result, tokens = call_llm(prompt)

    requirements = result.get("requirements", [])
    use_cases = result.get("use_cases", [])

    if not requirements:
        logger.error("[architect] extract_requirements — no requirements returned")
        return {
            **state,
            "requirements": [],
            "use_cases": [],
            "errors": state.get("errors", []) + [
                "extract_requirements: LLM returned no requirements"
            ],
            "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
        }

    logger.info(
        "[architect] extract_requirements — %d FRs/NFRs, %d use cases",
        len(requirements),
        len(use_cases),
    )

    return {
        **state,
        "requirements": requirements,
        "use_cases": use_cases,
        "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
    }
