"""Retry helpers for the Marketing Agent (AF-044)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_async(
    fn: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    label: str = "operation",
    **kwargs: Any,
) -> T:
    """Execute an async callable with exponential backoff retries.

    Args:
        fn: Async callable to retry.
        *args: Positional args forwarded to fn.
        max_retries: Maximum number of attempts.
        backoff_base: Base seconds for exponential backoff.
        label: Human-readable name for logging.
        **kwargs: Keyword args forwarded to fn.

    Returns:
        Result of fn on success.

    Raises:
        The last exception if all retries fail.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "[marketing] %s failed (attempt %d/%d): %s",
                label,
                attempt,
                max_retries,
                exc,
            )
            if attempt < max_retries:
                sleep_for = backoff_base**attempt
                await asyncio.sleep(sleep_for)

    raise last_exc  # type: ignore[misc]
