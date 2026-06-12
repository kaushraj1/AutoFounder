import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger("app.agents.strategy.llm_parse")


async def parse_with_correction(
    agent: Any,
    task_class: str,
    raw_output: str,
    schema: type[T],
    original_prompt: str,
    max_corrections: int = 1,
) -> T:
    """
    Attempt to parse LLM output as schema T.
    On failure, ask the LLM to self-correct once before raising.
    """
    current_output = raw_output
    for attempt in range(max_corrections + 1):
        try:
            cleaned = current_output.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            data = json.loads(cleaned)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            # Try to recover if the LLM wrapped a list inside a dict (e.g. {"personas": [...]})
            if isinstance(exc, ValidationError) and 'data' in locals() and isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list):
                        try:
                            return schema.model_validate(val)
                        except ValidationError:
                            continue
                # Try wrapping a single dict in a list if the schema expects a list
                try:
                    return schema.model_validate([data])
                except ValidationError:
                    pass

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
