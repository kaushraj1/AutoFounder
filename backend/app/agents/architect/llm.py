"""LLM call helper for the Architect Agent (AF-040).

Wraps Google Gemini (via google-generativeai) with:
- JSON-mode enforcement
- Token counting
- Retry (3 attempts, exponential backoff)
- Standalone mode: uses GEMINI_API_KEY env var directly,
  no LiteLLM router needed yet (Purnima wires that in Phase 2).

Install deps:
    uv sync --group agents
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gemini-1.5-flash"
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0  # seconds


def call_llm(
    prompt: str,
    *,
    model: str = _DEFAULT_MODEL,
    temperature: float = 0.2,
    max_retries: int = _MAX_RETRIES,
) -> tuple[dict[str, Any], int]:
    """Call Gemini and return (parsed_json_dict, tokens_used).

    The prompt MUST instruct the model to return only valid JSON.
    Raises RuntimeError if all retries fail or JSON cannot be parsed.
    """
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "google-generativeai not installed. Run: uv sync --group agents"
        ) from exc

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    genai.configure(api_key=api_key)
    client = genai.GenerativeModel(model)

    generation_config = genai.types.GenerationConfig(
        temperature=temperature,
        response_mime_type="application/json",
    )

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.generate_content(
                prompt,
                generation_config=generation_config,
            )
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw)
            tokens = getattr(response.usage_metadata, "total_token_count", 0)
            return parsed, tokens
        except json.JSONDecodeError as exc:
            logger.warning("Attempt %d: JSON parse error — %s", attempt, exc)
            last_exc = exc
        except Exception as exc:
            logger.warning("Attempt %d: LLM call failed — %s", attempt, exc)
            last_exc = exc

        if attempt < max_retries:
            sleep_for = _BACKOFF_BASE ** attempt
            logger.info("Retrying in %.1f s...", sleep_for)
            time.sleep(sleep_for)

    raise RuntimeError(
        f"LLM call failed after {max_retries} attempts: {last_exc}"
    )
