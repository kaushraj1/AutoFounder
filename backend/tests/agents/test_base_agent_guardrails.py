"""BaseAgent <-> AF-046 guardrails wiring (additive, opt-in)."""

from __future__ import annotations

from typing import Any

import pytest

from app.agents.base import BaseAgent, LLMError, ToolError
from app.guardrails.schema import GuardrailStage, GuardResult


class FakeGuards:
    """Records invocations; optionally blocks or redacts."""

    def __init__(self, *, block_llm: bool = False, block_tool: bool = False, redact: bool = False):
        self.block_llm = block_llm
        self.block_tool = block_tool
        self.redact = redact
        self.before_calls: list[Any] = []
        self.tool_calls: list[Any] = []

    async def before_llm(self, ctx: Any, payload: dict[str, Any]) -> GuardResult:
        self.before_calls.append((ctx, payload))
        if self.block_llm:
            return GuardResult.block(GuardrailStage.input, "blocked llm")
        if self.redact:
            return GuardResult.ok(GuardrailStage.input, {**payload, "prompt": "[REDACTED]"})
        return GuardResult.ok(GuardrailStage.input, payload)

    async def around_tool(self, ctx: Any, tool_call: dict[str, Any]) -> GuardResult:
        self.tool_calls.append((ctx, tool_call))
        if self.block_tool:
            return GuardResult.block(GuardrailStage.execution, "blocked tool")
        return GuardResult.ok(GuardrailStage.execution, tool_call)

    async def after_llm(self, ctx: Any, output: Any) -> GuardResult:
        return GuardResult.ok(GuardrailStage.output)


class FakeTools:
    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        return {"result": tool_name}


class FakePrompts:
    def get(self, key: str, version: str | None = None) -> str:
        return key


class FakeLLM:
    def __init__(self) -> None:
        self.last_prompt: str | None = None

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        self.last_prompt = prompt
        return "response"


class DummyAgent(BaseAgent[dict[str, Any], dict[str, Any]]):
    PILLAR = 1
    AGENT_ID = "dummy.guard"
    SLA_SECONDS = 5

    async def understand(self, input: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def verify(self, output: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def learn(self, trace: dict[str, Any]) -> None:
        return None


def _agent(guards: FakeGuards | None) -> tuple[DummyAgent, FakeLLM]:
    llm = FakeLLM()
    agent = DummyAgent(None, None, FakeTools(), FakePrompts(), llm, guardrails=guards)
    return agent, llm


async def test_before_llm_invoked_and_sanitizes() -> None:
    guards = FakeGuards(redact=True)
    agent, llm = _agent(guards)
    out = await agent._call_llm(task_class="c", prompt="my email is a@b.com")
    assert out == "response"
    assert guards.before_calls  # guardrail ran
    assert llm.last_prompt == "[REDACTED]"  # sanitized prompt forwarded


async def test_blocked_llm_raises() -> None:
    agent, _ = _agent(FakeGuards(block_llm=True))
    with pytest.raises(LLMError, match="Guardrail blocked"):
        await agent._call_llm(task_class="c", prompt="hi")


async def test_blocked_tool_raises() -> None:
    agent, _ = _agent(FakeGuards(block_tool=True))
    with pytest.raises(ToolError, match="Guardrail blocked"):
        await agent._call_tool("some_tool", {"a": 1})


async def test_tool_passes_when_not_blocked() -> None:
    guards = FakeGuards()
    agent, _ = _agent(guards)
    result = await agent._call_tool("some_tool", {"a": 1})
    assert result == {"result": "some_tool"}
    assert guards.tool_calls


async def test_default_none_guardrails_is_passthrough() -> None:
    agent, llm = _agent(None)  # no guardrails -> unchanged behavior
    assert await agent._call_llm(task_class="c", prompt="hello") == "response"
    assert await agent._call_tool("t", {}) == {"result": "t"}
    assert llm.last_prompt == "hello"
