"""Retry-decorator tests."""

import pytest

from app.agents.devops.schema import RetryPolicy
from app.agents.devops.utils.retry import with_retry


@pytest.mark.asyncio
async def test_with_retry_succeeds_after_retry() -> None:
    attempts = {"n": 0}

    @with_retry(RetryPolicy(max_retries=1, backoff_seconds=[0]))
    async def flaky() -> str:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ValueError("fail once")
        return "ok"

    assert await flaky() == "ok"
    assert attempts["n"] == 2


@pytest.mark.asyncio
async def test_with_retry_raises_after_exhaustion() -> None:
    @with_retry(RetryPolicy(max_retries=1, backoff_seconds=[0]))
    async def always_fail() -> str:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await always_fail()
