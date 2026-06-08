"""enforce_node_sla decorator: per-node timeout via asyncio.wait_for."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import TypeVar

T = TypeVar("T")


def enforce_node_sla(
    seconds: float,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(fn)
        async def wrapper(*args: object, **kwargs: object) -> T:
            return await asyncio.wait_for(fn(*args, **kwargs), timeout=seconds)

        return wrapper

    return decorator