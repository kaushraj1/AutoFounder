"""with_retry decorator: retries an async callable per the given RetryPolicy."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import TypeVar

from ..schema import RetryPolicy

T = TypeVar("T")


def with_retry(
    policy: RetryPolicy,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(fn)
        async def wrapper(*args: object, **kwargs: object) -> T:
            attempts = policy.max_retries + 1
            for i in range(attempts):
                try:
                    return await fn(*args, **kwargs)
                except Exception:
                    if i == attempts - 1:
                        raise
                    backoff = policy.backoff_seconds[min(i, len(policy.backoff_seconds) - 1)]
                    await asyncio.sleep(backoff)
            raise RuntimeError("unreachable")

        return wrapper

    return decorator