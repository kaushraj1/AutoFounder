"""LLM JSON helper for DevOps nodes.

Mirrors the strategy agent's parse_with_correction: strips Markdown fences,
attempts ``schema.model_validate`` once, and on failure asks the LLM to
self-correct exactly once before raising.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger("app.agents.devops.llm_json")


def _strip_fence(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


async def parse_with_correction(
    *,
    agent: Any,
    task_class: str,
    raw_output: str,
    schema: type[T],
    original_prompt: str,
    max_corrections: int = 1,
) -> T:
    current = raw_output
    for attempt in range(max_corrections + 1):
        try:
            return schema.model_validate(json.loads(_strip_fence(current)))
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt >= max_corrections:
                logger.error(
                    "DevOps LLM output failed validation after %d corrections: %s",
                    attempt,
                    exc,
                )
                raise
            logger.warning(
                "DevOps parse error on attempt %d, requesting self-correction: %s",
                attempt,
                exc,
            )
            correction_prompt = (
                f"Your previous output failed JSON/Pydantic validation.\n"
                f"Error: {exc}\n"
                f"Previous output:\n{current}\n\n"
                f"Return ONLY corrected JSON matching the required schema. "
                f"No markdown, no explanation."
            )
            current = await agent._call_llm(
                task_class=task_class, prompt=correction_prompt, json_mode=True
            )
    raise ValueError("unreachable")
