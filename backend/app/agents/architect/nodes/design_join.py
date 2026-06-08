"""Node 3 — design_join (AF-040).

Barrier node — waits for ERD, OpenAPI, and stack to all be present
before letting the graph continue. Writes design_complete = True.

Reads: erd_mermaid, openapi_3_1, stack
Writes: design_complete
"""

from __future__ import annotations

import logging

from app.agents.architect.state import ArchitectState

logger = logging.getLogger(__name__)


def design_join(state: ArchitectState) -> ArchitectState:
    """LangGraph node: barrier — verify all three parallel designs are present."""
    logger.info("[architect] design_join — checking parallel outputs")

    errors = list(state.get("errors", []))
    missing = []

    if not state.get("erd_mermaid"):
        missing.append("erd_mermaid")
    if not state.get("openapi_3_1"):
        missing.append("openapi_3_1")
    if not state.get("stack"):
        missing.append("stack")

    if missing:
        msg = f"design_join: parallel design outputs missing: {', '.join(missing)}"
        logger.error("[architect] %s", msg)
        errors.append(msg)

    logger.info("[architect] design_join — all parallel outputs present, continuing")

    return {
        **state,
        "design_complete": len(missing) == 0,
        "errors": errors,
    }
