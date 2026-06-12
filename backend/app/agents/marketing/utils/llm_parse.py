"""LLM JSON parse-with-correction helper for the Marketing Agent (AF-044).

If the LLM returns malformed JSON, this helper asks the LLM to fix it
with a single correction pass before raising an error.
"""

from __future__ import annotations

import json
import logging
from typing import Any

# Import at module level so tests can patch app.agents.marketing.llm_parse.call_llm
try:
    from app.agents.marketing.llm import call_llm  # noqa: F401 (re-exported for patching)
except ImportError:
    call_llm = None  # type: ignore[assignment]  # tests inject via patch

logger = logging.getLogger(__name__)


async def parse_with_correction(
    raw: str,
    original_prompt: str,
    *,
    max_correction_attempts: int = 1,
) -> dict[str, Any]:
    """Parse LLM output as JSON, with one correction retry on failure.

    Args:
        raw: Raw string output from the LLM.
        original_prompt: The prompt that produced the raw output (used for correction).
        max_correction_attempts: How many times to retry with a correction prompt.

    Returns:
        Parsed JSON dict.

    Raises:
        ValueError: If JSON cannot be parsed after correction attempts.
    """
    # Strip markdown fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        if len(parts) >= 2:
            cleaned = parts[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as original_exc:
        logger.warning("[marketing] JSON parse failed, attempting correction: %s", original_exc)

        if max_correction_attempts <= 0:
            raise ValueError(f"LLM JSON parse failed: {original_exc}") from original_exc

        # Ask the LLM to correct its own output
        from app.agents.marketing import (
            llm as _llm_module,  # allows patching via `app.agents.marketing.llm.call_llm`
        )

        correction_prompt = (
            f"The following JSON output is invalid. Fix ONLY the JSON syntax — "
            f"do not change the content. Return ONLY valid JSON, nothing else.\n\n"
            f"Invalid JSON:\n{raw}\n\n"
            f"Error: {original_exc}"
        )

        try:
            result, _ = await _llm_module.call_llm(correction_prompt, temperature=0.0)
            logger.info("[marketing] JSON correction succeeded")
            return result
        except Exception as correction_exc:
            raise ValueError(
                f"LLM JSON correction also failed: {correction_exc}"
            ) from correction_exc
