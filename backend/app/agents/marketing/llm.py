"""Async LLM call helper for the Marketing Agent (AF-044).

Wraps Google Gemini (via google-generativeai) with:
- Async execution (required for parallel LangGraph nodes)
- JSON-mode enforcement
- Token counting
- Retry with exponential backoff (3 attempts)
- Standalone: uses GEMINI_API_KEY env var directly (no LiteLLM router needed until AF-049)

Usage:
    result, tokens = await call_llm(prompt)
    result, tokens = await call_llm(prompt, model="gemini-1.5-pro", temperature=0.4)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gemini-1.5-flash"
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0


async def call_llm(
    prompt: str,
    *,
    model: str = _DEFAULT_MODEL,
    temperature: float = 0.2,
    max_retries: int = _MAX_RETRIES,
) -> tuple[dict[str, Any], int]:
    """Call Gemini asynchronously and return (parsed_json_dict, tokens_used).

    The prompt MUST instruct the model to return only valid JSON.
    Raises RuntimeError if all retries fail or JSON cannot be parsed.
    """
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "google-generativeai not installed. Run: uv sync"
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
            # Run the synchronous SDK call in a thread pool to keep async
            response = await asyncio.to_thread(
                client.generate_content,
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
            logger.debug(
                "[marketing] llm call — attempt=%d tokens=%d model=%s",
                attempt,
                tokens,
                model,
            )
            return parsed, tokens

        except json.JSONDecodeError as exc:
            logger.warning("[marketing] LLM JSON parse error attempt %d: %s", attempt, exc)
            last_exc = exc
        except Exception as exc:
            logger.warning("[marketing] LLM call failed attempt %d: %s", attempt, exc)
            last_exc = exc

        if attempt < max_retries:
            sleep_for = _BACKOFF_BASE**attempt
            logger.info("[marketing] Retrying LLM in %.1f s...", sleep_for)
            await asyncio.sleep(sleep_for)

    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_exc}")


async def call_llm_text(
    prompt: str,
    *,
    model: str = _DEFAULT_MODEL,
    temperature: float = 0.4,
    max_retries: int = _MAX_RETRIES,
) -> tuple[str, int]:
    """Call Gemini and return (raw_text, tokens_used) for non-JSON outputs (e.g. Markdown)."""
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError("google-generativeai not installed.") from exc

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    genai.configure(api_key=api_key)
    client = genai.GenerativeModel(model)

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = await asyncio.to_thread(
                client.generate_content,
                prompt,
            )
            raw = response.text.strip()
            tokens = getattr(response.usage_metadata, "total_token_count", 0)
            return raw, tokens
        except Exception as exc:
            logger.warning("[marketing] LLM text call failed attempt %d: %s", attempt, exc)
            last_exc = exc
            if attempt < max_retries:
                await asyncio.sleep(_BACKOFF_BASE**attempt)

    raise RuntimeError(f"LLM text call failed after {max_retries} attempts: {last_exc}")
