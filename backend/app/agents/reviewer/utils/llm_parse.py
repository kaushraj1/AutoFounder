"""LLM output parsing with one self-correction pass (plan fallback matrix).

Mirrors ``app.agents.strategy.utils.llm_parse`` so the Reviewer's judge / triage
/ heal nodes recover from a single malformed-JSON response before escalating.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger("app.agents.reviewer.llm_parse")


def strip_code_fences(raw: str) -> str:
    """Remove a leading/trailing markdown ``` fence if the model added one."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def loads_lenient(raw: str) -> Any:
    """Parse JSON, tolerating markdown code fences. Raises on hard failure."""
    return json.loads(strip_code_fences(raw))


async def parse_with_correction(
    agent: Any,
    task_class: str,
    raw_output: str,
    schema: type[T],
    original_prompt: str,
    max_corrections: int = 1,
) -> T:
    """Parse LLM output as schema ``T``; ask the model to self-correct once."""
    current_output = raw_output
    for attempt in range(max_corrections + 1):
        try:
            data = loads_lenient(current_output)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt >= max_corrections:
                logger.error("LLM output failed validation after %d corrections: %s", attempt, exc)
                raise
            logger.warning(
                "Parse error on attempt %d, requesting self-correction: %s", attempt, exc
            )
            correction_prompt = (
                f"Your previous output failed JSON/Pydantic validation:\n"
                f"Error: {exc}\n"
                f"Previous output:\n{current_output}\n\n"
                f"Return ONLY corrected JSON matching the required schema. "
                f"No markdown, no explanation."
            )
            current_output = await agent._call_llm(
                task_class=task_class, prompt=correction_prompt, json_mode=True
            )
    raise ValueError("Unexpected loop exit in parse_with_correction")
