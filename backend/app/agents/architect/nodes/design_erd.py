"""Node 2a — design_erd (AF-040).  Runs in parallel with 2b + 2c.

Reads: requirements[], use_cases[]
Writes: erd_mermaid, erd_entities[], erd_indexes[], erd_design_notes
"""

from __future__ import annotations

import logging

from app.agents.architect.llm import call_llm
from app.agents.architect.prompt_loader import render
from app.agents.architect.state import ArchitectState
from app.agents.architect.tools.mermaid import MermaidTool

logger = logging.getLogger(__name__)
_mermaid = MermaidTool()


def design_erd(state: ArchitectState) -> ArchitectState:
    """LangGraph node: generate a Mermaid ERD from requirements."""
    logger.info("[architect] design_erd — start")

    prompt = render(
        "design_erd",
        requirements=state.get("requirements", []),
        use_cases=state.get("use_cases", []),
    )

    result, tokens = call_llm(prompt)

    erd_mermaid: str = result.get("erd_mermaid", "")
    entities: list[str] = result.get("entities", [])
    indexes: list[dict] = result.get("indexes", [])
    design_notes: str = result.get("design_notes", "")

    # Validate the generated ERD
    validation = _mermaid.validate(erd_mermaid)
    errors = list(state.get("errors", []))

    if not validation.valid:
        for err in validation.errors:
            logger.warning("[architect] design_erd — ERD validation: %s", err)
            errors.append(f"design_erd: {err}")

    # Use entity list from validator if LLM omitted it
    if not entities and validation.entities:
        entities = validation.entities

    logger.info(
        "[architect] design_erd — %d entities, %d relationships, valid=%s",
        validation.entity_count,
        validation.relationship_count,
        validation.valid,
    )

    return {
        **state,
        "erd_mermaid": erd_mermaid,
        "erd_entities": entities,
        "erd_indexes": indexes,
        "erd_design_notes": design_notes,
        "errors": errors,
        "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
    }
