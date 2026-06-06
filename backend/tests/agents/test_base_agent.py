import asyncio
from typing import Any

import pytest

from app.agents.base import (
    AgentError,
    BaseAgent,
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    ExecuteError,
    LearnError,
    LLMError,
    PlanError,
    SLAExceededError,
    ToolError,
    UnderstandError,
    VerifyError,
)


class FakeToolRegistry:
    def __init__(self) -> None:
        self.should_fail = False
        self.called_with = None

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        self.called_with = (tool_name, args)
        if self.should_fail:
            raise Exception("Tool failed")
        return {"result": f"Executed {tool_name}"}


class FakePromptRegistry:
    def get(self, key: str, version: str | None = None) -> str:
        return f"template for {key}"


class FakeLLMRouter:
    def __init__(self) -> None:
        self.should_fail = False
        self.called_with = None

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        self.called_with = (task_class, prompt, kw)
        if self.should_fail:
            raise Exception("LLM failed")
        return "LLM response"


class DummyAgent(BaseAgent[dict[str, Any], dict[str, Any]]):
    PILLAR = 1
    AGENT_ID = "dummy.v1"
    SLA_SECONDS = 2  # Keep it small for testing timeouts

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.call_order = []
        self.understand_fail = False
        self.plan_fail = False
        self.execute_fail = False
        self.verify_fail = False
        self.learn_fail = False
        self.execute_delay = 0.0

    async def understand(self, input: dict[str, Any]) -> dict[str, Any]:
        self.call_order.append("understand")
        if self.understand_fail:
            raise Exception("Understand error")
        return {"intent": "dummy_intent"}

    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        self.call_order.append("plan")
        if self.plan_fail:
            raise Exception("Plan error")
        return {"steps": ["step1"]}

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        self.call_order.append("execute")
        if self.execute_delay > 0:
            await asyncio.sleep(self.execute_delay)
        if self.execute_fail:
            raise Exception("Execute error")
        return {"output": "dummy_output"}

    async def verify(self, output: dict[str, Any]) -> dict[str, Any]:
        self.call_order.append("verify")
        if self.verify_fail:
            raise Exception("Verify error")
        return {"verified": True}

    async def learn(self, trace: dict[str, Any]) -> None:
        self.call_order.append("learn")
        if self.learn_fail:
            raise Exception("Learn error")


@pytest.fixture
def base_dependencies():
    return (
        None,  # udal
        None,  # checkpointer
        FakeToolRegistry(),
        FakePromptRegistry(),
        FakeLLMRouter(),
    )


@pytest.mark.asyncio
async def test_circuit_breaker_flow():
    # T-CB1, T-CB2, T-CB3
    failures = 0

    async def dummy_fn():
        nonlocal failures
        if failures < 2:
            failures += 1
            raise ValueError("Call fail")
        return "success"

    cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1, name="test_breaker")

    # 1.CLOSED state initially
    assert cb.state == CircuitState.CLOSED

    # Call 1 fails
    with pytest.raises(ValueError):
        await cb.call(dummy_fn)
    assert cb.state == CircuitState.CLOSED
    assert cb.failures == 1

    # Call 2 fails -> state -> OPEN
    with pytest.raises(ValueError):
        await cb.call(dummy_fn)
    assert cb.state == CircuitState.OPEN
    assert cb.failures == 2

    # Call 3 (immediate) -> rejects with CircuitOpenError
    with pytest.raises(CircuitOpenError):
        await cb.call(dummy_fn)

    # Wait for reset timeout
    await asyncio.sleep(0.15)

    # Call 4 -> transitions to HALF_OPEN, succeeds -> CLOSED
    res = await cb.call(dummy_fn)
    assert res == "success"
    assert cb.state == CircuitState.CLOSED
    assert cb.failures == 0


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure():
    # If HALF_OPEN call fails, transitions back to OPEN
    async def failing_fn():
        raise ValueError("Fail again")

    cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.05, name="test_breaker_fail")
    with pytest.raises(ValueError):
        await cb.call(failing_fn)
    assert cb.state == CircuitState.OPEN

    await asyncio.sleep(0.06)
    # now in HALF_OPEN, try calling failing_fn
    with pytest.raises(ValueError):
        await cb.call(failing_fn)
    # should be back to OPEN immediately
    assert cb.state == CircuitState.OPEN


def test_error_hierarchy():
    # T-ERR
    err = AgentError("general error", agent_id="agent1", run_id="run1")
    assert err.agent_id == "agent1"
    assert err.run_id == "run1"
    assert isinstance(err, Exception)

    sub_errs = [
        UnderstandError,
        PlanError,
        ExecuteError,
        VerifyError,
        LearnError,
        ToolError,
        LLMError,
        SLAExceededError,
    ]
    for sub_err in sub_errs:
        se = sub_err("msg", agent_id="agent1", run_id="run1")
        assert isinstance(se, AgentError)
        assert se.agent_id == "agent1"
        assert se.run_id == "run1"

    # CircuitOpenError carries custom name
    coe = CircuitOpenError("msg", name="my_breaker", agent_id="agent1", run_id="run1")
    assert isinstance(coe, AgentError)
    assert coe.name == "my_breaker"


def test_subclass_enforcement(base_dependencies):
    # T8, T-ATTR

    # Missing PILLAR
    with pytest.raises(AttributeError, match="must define class attribute 'PILLAR'"):

        class NoPillarAgent(BaseAgent):
            AGENT_ID = "no_pillar"
            SLA_SECONDS = 10

            async def understand(self, input):
                pass

            async def plan(self, intent):
                pass

            async def execute(self, plan):
                pass

            async def verify(self, output):
                pass

            async def learn(self, trace):
                pass

    # Invalid AGENT_ID type
    with pytest.raises(TypeError, match="class attribute 'AGENT_ID' must be of type str"):

        class BadAgentIdAgent(BaseAgent):
            PILLAR = 1
            AGENT_ID = 123

            async def understand(self, input):
                pass

            async def plan(self, intent):
                pass

            async def execute(self, plan):
                pass

            async def verify(self, output):
                pass

            async def learn(self, trace):
                pass

    # Missing abstract methods
    with pytest.raises(TypeError):

        class IncompleteAgent(BaseAgent):
            PILLAR = 1
            AGENT_ID = "incomplete"
            SLA_SECONDS = 10

        # This will raise TypeError upon instantiation
        IncompleteAgent(*base_dependencies)


@pytest.mark.asyncio
async def test_base_agent_guarded_calls(base_dependencies):
    # T-LLM, T-TOOL
    udal, checkpointer, tools, prompts, llm = base_dependencies
    agent = DummyAgent(udal, checkpointer, tools, prompts, llm, breaker_failure_threshold=1)

    # 1. Guarded LLM call happy path
    res = await agent._call_llm(task_class="class1", prompt="hello")
    assert res == "LLM response"
    assert llm.called_with == ("class1", "hello", {})

    # 2. Guarded LLM call failure -> LLMError + Breaker OPEN
    llm.should_fail = True
    with pytest.raises(LLMError):
        await agent._call_llm(task_class="class1", prompt="hello")
    assert agent._llm_breaker.state == CircuitState.OPEN

    # 3. Guarded tool call happy path
    res = await agent._call_tool(tool_name="tool1", args={"a": 1})
    assert res == {"result": "Executed tool1"}
    assert tools.called_with == ("tool1", {"a": 1})

    # 4. Guarded tool call failure -> ToolError + Breaker OPEN
    tools.should_fail = True
    with pytest.raises(ToolError):
        await agent._call_tool(tool_name="tool1", args={"a": 1})
    assert agent._tool_breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_base_agent_run_happy_path(base_dependencies):
    # T-RUN
    udal, checkpointer, tools, prompts, llm = base_dependencies
    agent = DummyAgent(udal, checkpointer, tools, prompts, llm)

    res = await agent.run({"organization_id": "org123", "run_id": "run456"})
    assert res == {"output": "dummy_output"}
    assert agent.call_order == ["understand", "plan", "execute", "verify", "learn"]


@pytest.mark.asyncio
async def test_base_agent_run_phase_failures(base_dependencies):
    # Enforces exception mapping to phase-specific errors
    udal, checkpointer, tools, prompts, llm = base_dependencies

    # 1. Understand fails
    agent = DummyAgent(udal, checkpointer, tools, prompts, llm)
    agent.understand_fail = True
    with pytest.raises(UnderstandError):
        await agent.run({"organization_id": "org123", "run_id": "run456"})
    assert agent.call_order == ["understand", "learn"]

    # 2. Plan fails
    agent = DummyAgent(udal, checkpointer, tools, prompts, llm)
    agent.plan_fail = True
    with pytest.raises(PlanError):
        await agent.run({"organization_id": "org123", "run_id": "run456"})
    assert agent.call_order == ["understand", "plan", "learn"]

    # 3. Execute fails
    agent = DummyAgent(udal, checkpointer, tools, prompts, llm)
    agent.execute_fail = True
    with pytest.raises(ExecuteError):
        await agent.run({"organization_id": "org123", "run_id": "run456"})
    assert agent.call_order == ["understand", "plan", "execute", "learn"]

    # 4. Verify fails
    agent = DummyAgent(udal, checkpointer, tools, prompts, llm)
    agent.verify_fail = True
    with pytest.raises(VerifyError):
        await agent.run({"organization_id": "org123", "run_id": "run456"})
    assert agent.call_order == ["understand", "plan", "execute", "verify", "learn"]


@pytest.mark.asyncio
async def test_base_agent_run_learn_failure_non_fatal(base_dependencies):
    # Learn failure is logged but doesn't crash run()
    udal, checkpointer, tools, prompts, llm = base_dependencies
    agent = DummyAgent(udal, checkpointer, tools, prompts, llm)
    agent.learn_fail = True

    res = await agent.run({"organization_id": "org123", "run_id": "run456"})
    assert res == {"output": "dummy_output"}
    assert agent.call_order == ["understand", "plan", "execute", "verify", "learn"]


@pytest.mark.asyncio
async def test_base_agent_run_timeout(base_dependencies):
    # T-SLA
    udal, checkpointer, tools, prompts, llm = base_dependencies
    agent = DummyAgent(udal, checkpointer, tools, prompts, llm)
    agent.execute_delay = 3.0  # agent.SLA_SECONDS is 2.0

    with pytest.raises(SLAExceededError):
        await agent.run({"organization_id": "org123", "run_id": "run456"})
    assert agent.call_order == ["understand", "plan", "execute", "learn"]
