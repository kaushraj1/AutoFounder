"""Node 2b — design_api_contract (AF-040).  Runs in parallel with 2a + 2c.

Reads: requirements[], erd_mermaid, erd_entities[]
Writes: openapi_3_1, openapi_valid, openapi_errors[]
"""

from __future__ import annotations

import logging

from app.agents.architect.llm import call_llm
from app.agents.architect.prompt_loader import render
from app.agents.architect.state import ArchitectState
from app.agents.architect.tools.openapi_validate import OpenAPIValidateTool

logger = logging.getLogger(__name__)
_validator = OpenAPIValidateTool()


def design_api_contract(state: ArchitectState) -> ArchitectState:
    """LangGraph node: generate an OpenAPI 3.1 spec from requirements + ERD."""
    logger.info("[architect] design_api_contract — start")

    prompt = render(
        "design_api_contract",
        requirements=state.get("requirements", []),
        erd_mermaid=state.get("erd_mermaid", ""),
        entities=state.get("erd_entities", []),
    )

    result, tokens = call_llm(prompt)

    # Validate immediately
    validation = _validator.validate(result)
    errors = list(state.get("errors", []))

    if not validation.valid:
        logger.warning(
            "[architect] design_api_contract — OpenAPI invalid (%d errors), re-prompting once",
            len(validation.errors),
        )
        # Re-prompt once with validation errors appended
        fix_prompt = (
            prompt
            + "\n\n---\nYour previous response had these OpenAPI validation errors. "
            "Fix them and return a corrected spec:\n"
            + "\n".join(f"- {e}" for e in validation.errors)
        )
        result, fix_tokens = call_llm(fix_prompt)
        tokens += fix_tokens
        validation = _validator.validate(result)

        if not validation.valid:
            for err in validation.errors:
                errors.append(f"design_api_contract: {err}")
            logger.error("[architect] design_api_contract — still invalid after re-prompt")

    logger.info(
        "[architect] design_api_contract — %d paths, %d schemas, valid=%s",
        validation.path_count,
        validation.schema_count,
        validation.valid,
    )

    return {
        **state,
        "openapi_3_1": result,
        "openapi_valid": validation.valid,
        "openapi_errors": validation.errors,
        "errors": errors,
        "llm_tokens_used": state.get("llm_tokens_used", 0) + tokens,
    }
