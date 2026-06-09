"""Unit — LLM output parsing + one-shot self-correction."""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from app.agents.reviewer.utils.llm_parse import (
    loads_lenient,
    parse_with_correction,
    strip_code_fences,
)


class _Model(BaseModel):
    value: int


class _FakeAgent:
    def __init__(self, correction: str) -> None:
        self.correction = correction
        self.calls = 0

    async def _call_llm(self, *, task_class: str, prompt: str, **kw) -> str:
        self.calls += 1
        return self.correction


def test_strip_code_fences() -> None:
    assert strip_code_fences('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert loads_lenient('```\n{"value": 5}\n```') == {"value": 5}


async def test_parse_valid_first_try() -> None:
    agent = _FakeAgent('{"value": 1}')
    result = await parse_with_correction(agent, "t", '{"value": 9}', _Model, "prompt")
    assert result.value == 9
    assert agent.calls == 0


async def test_parse_self_corrects_once() -> None:
    agent = _FakeAgent('{"value": 7}')
    result = await parse_with_correction(agent, "t", "not json", _Model, "prompt")
    assert result.value == 7
    assert agent.calls == 1


async def test_parse_raises_after_max_corrections() -> None:
    agent = _FakeAgent("still not json")
    with pytest.raises(json.JSONDecodeError):
        await parse_with_correction(agent, "t", "bad", _Model, "prompt")
