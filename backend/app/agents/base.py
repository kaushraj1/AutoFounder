"""Agent contract (CLAUDE.md §7.3).

Every specialized agent implements the same five-method loop:
``Understand -> Plan -> Execute -> Verify -> Learn``.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel, Field

from app.db.context import get_tenant_context

# --- Legacy Models and Agent Class (for backward compatibility) ---


class AgentInput(BaseModel):
    """Raw input handed to an agent."""

    organization_id: str
    payload: dict[str, object] = Field(default_factory=dict)


class Intent(BaseModel):
    """A structured interpretation of the input."""

    summary: str


class Step(BaseModel):
    """One atomic unit of work in a plan."""

    id: str
    description: str


class Plan(BaseModel):
    """An ordered DAG of steps (linear list in Phase 1)."""

    steps: list[Step] = Field(default_factory=list)


class StepEvent(BaseModel):
    """An event emitted as a step progresses."""

    step_id: str
    status: str


class AgentOutput(BaseModel):
    """The agent's produced output."""

    data: dict[str, object] = Field(default_factory=dict)


class VerifyResult(BaseModel):
    """Result of the agent's self-critique pass."""

    passed: bool
    issues: list[str] = Field(default_factory=list)


class ExecutionTrace(BaseModel):
    """A full run trace emitted to the LLMOps learning loop."""

    run_id: str
    events: list[StepEvent] = Field(default_factory=list)


class Agent(ABC):
    """Base class for all specialized agents (legacy)."""

    id: str
    capabilities: list[str]

    @abstractmethod
    async def understand(self, agent_input: AgentInput) -> Intent:
        """Parse raw input into a structured intent."""

    @abstractmethod
    async def plan(self, intent: Intent) -> Plan:
        """Decompose an intent into an ordered plan of atomic steps."""

    @abstractmethod
    async def execute(self, plan: Plan) -> list[StepEvent]:
        """Execute the plan. Phase 1 returns the full event list; streaming added in Sprint 1."""

    @abstractmethod
    async def verify(self, output: AgentOutput) -> VerifyResult:
        """Self-critique the output before returning it."""

    @abstractmethod
    async def learn(self, trace: ExecutionTrace) -> None:
        """Emit the execution trace to the LLMOps learning loop."""


# --- New AF-036 BaseAgent ABC implementation ---

# Type variables
TIn = TypeVar("TIn")
TOut = TypeVar("TOut")
T = TypeVar("T")


# Circuit Breaker Implementation


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Async circuit breaker for LLM + tool calls.

    failure_threshold consecutive failures -> OPEN; after reset_timeout -> HALF_OPEN;
    one success in HALF_OPEN -> CLOSED. OPEN rejects with CircuitOpenError (fail-fast).
    """

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        reset_timeout: float = 30.0,
        name: str = "breaker",
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.name = name
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = 0.0

    async def call(self, fn: Callable[..., Awaitable[T]], *a: Any, **kw: Any) -> T:
        now = time.monotonic()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time > self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(
                    f"Circuit breaker '{self.name}' is OPEN",
                    name=self.name,
                )

        try:
            res = await fn(*a, **kw)
            # Success path
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failures = 0
            elif self.state == CircuitState.CLOSED:
                self.failures = 0
            return res
        except Exception as e:
            # Failure path
            if isinstance(e, CircuitOpenError):
                raise e
            self.failures += 1
            self.last_failure_time = time.monotonic()
            if self.state == CircuitState.HALF_OPEN or self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
            raise e


# Typed Error Hierarchy


class AgentError(Exception):
    """Root of all agent failures. Carries observability context."""

    def __init__(
        self,
        message: str,
        *,
        agent_id: str | None = None,
        run_id: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.agent_id = agent_id
        self.run_id = run_id
        self.cause = cause


class UnderstandError(AgentError):
    """Input parse / intent failure."""


class PlanError(AgentError):
    """Decomposition failure."""


class ExecuteError(AgentError):
    """Step execution failure."""


class VerifyError(AgentError):
    """Self-critique hard failure."""


class LearnError(AgentError):
    """Trace emit failure (non-fatal upstream)."""


class ToolError(AgentError):
    """Tool call failed."""


class LLMError(AgentError):
    """Model call failed."""


class CircuitOpenError(AgentError):
    """Breaker rejected call (fail-fast)."""

    def __init__(
        self,
        message: str,
        name: str = "",
        *,
        agent_id: str | None = None,
        run_id: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message, agent_id=agent_id, run_id=run_id, cause=cause)
        self.name = name


class SLAExceededError(AgentError):
    """SLA_SECONDS budget blown."""


# Protocols (Contract-first DI)


class ToolRegistryProtocol(Protocol):
    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call a registered tool."""
        ...


class PromptRegistryProtocol(Protocol):
    def get(self, key: str, version: str | None = None) -> str:
        """Get prompt template."""
        ...


class LLMRouterProtocol(Protocol):
    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        """Route to LLM and execute completion."""
        ...


class GuardrailPipelineProtocol(Protocol):
    """The AF-046 guardrail wrapper (optional). Duck-typed to keep base decoupled."""

    async def before_llm(self, ctx: Any, payload: dict[str, Any]) -> Any:
        """Policy/Input/Instruction checks before an LLM call."""
        ...

    async def around_tool(self, ctx: Any, tool_call: dict[str, Any]) -> Any:
        """Execution-guard check around a tool call."""
        ...

    async def after_llm(self, ctx: Any, output: Any) -> Any:
        """Output/Monitoring checks after generation."""
        ...


# BaseAgent


class BaseAgent(ABC, Generic[TIn, TOut]):
    """Unified BaseAgent ABC for all specialized agents.

    Enforces subclass attributes (PILLAR, AGENT_ID, SLA_SECONDS) and provides
    circuit breakers, generic IO type checks, and SLA timing via run().
    """

    PILLAR: int
    AGENT_ID: str
    SLA_SECONDS: int = 1800  # Default to 30 min

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Verify required class attributes on concrete subclasses
        has_abstract = any(
            getattr(getattr(cls, name, None), "__isabstractmethod__", False) for name in dir(cls)
        )
        if not has_abstract:
            for attr, attr_type in [("PILLAR", int), ("AGENT_ID", str), ("SLA_SECONDS", int)]:
                if not hasattr(cls, attr):
                    raise AttributeError(
                        f"Class {cls.__name__} must define class attribute '{attr}'"
                    )
                val = getattr(cls, attr)
                if val is None or not isinstance(val, attr_type):
                    raise TypeError(
                        f"Class {cls.__name__} class attribute '{attr}' "
                        f"must be of type {attr_type.__name__}"
                    )

    def __init__(
        self,
        udal: Any,
        checkpointer: Any,
        tool_registry: ToolRegistryProtocol,
        prompt_registry: PromptRegistryProtocol,
        llm_router: LLMRouterProtocol,
        *,
        breaker_failure_threshold: int = 5,
        breaker_reset_timeout: float = 30.0,
        guardrails: GuardrailPipelineProtocol | None = None,
    ) -> None:
        # Re-check during instantiation just in case
        for attr, attr_type in [("PILLAR", int), ("AGENT_ID", str), ("SLA_SECONDS", int)]:
            if not hasattr(self, attr):
                raise AttributeError(f"Agent missing class attribute '{attr}'")
            val = getattr(self, attr)
            if val is None or not isinstance(val, attr_type):
                raise TypeError(
                    f"Agent class attribute '{attr}' must be of type {attr_type.__name__}"
                )

        self.udal = udal
        self.checkpointer = checkpointer
        self.tools = tool_registry
        self.prompts = prompt_registry
        self.llm = llm_router
        # AF-046 guardrails are optional: None => no wrapping (existing agents).
        self.guardrails = guardrails
        self._current_run_id: str | None = None
        self._llm_breaker = CircuitBreaker(
            name=f"{self.AGENT_ID}.llm",
            failure_threshold=breaker_failure_threshold,
            reset_timeout=breaker_reset_timeout,
        )
        self._tool_breaker = CircuitBreaker(
            name=f"{self.AGENT_ID}.tool",
            failure_threshold=breaker_failure_threshold,
            reset_timeout=breaker_reset_timeout,
        )

    def _guard_context(self) -> Any:
        """Build a per-call GuardrailContext from the current tenant + run."""
        from app.guardrails.schema import GuardrailContext

        return GuardrailContext(
            organization_id=get_tenant_context() or "unknown",
            run_id=self._current_run_id,
            agent_id=self.AGENT_ID,
        )

    async def _call_llm(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        """Guarded LLM call wrapper using circuit breaker (+ optional AF-046 guardrails)."""
        if self.guardrails is not None:
            verdict = await self.guardrails.before_llm(
                self._guard_context(),
                {"prompt": prompt, "task_class": task_class, "input": prompt},
            )
            if getattr(verdict, "blocked", False):
                raise LLMError(
                    f"Guardrail blocked LLM call: {getattr(verdict, 'reason', None)}",
                    agent_id=self.AGENT_ID,
                )
            sanitized = getattr(verdict, "sanitized_payload", None)
            if isinstance(sanitized, dict) and isinstance(sanitized.get("prompt"), str):
                prompt = sanitized["prompt"]
        try:
            return await self._llm_breaker.call(
                self.llm.complete, task_class=task_class, prompt=prompt, **kw
            )
        except CircuitOpenError as e:
            e.agent_id = self.AGENT_ID
            raise e
        except Exception as e:
            raise LLMError(f"LLM call failed: {e}", agent_id=self.AGENT_ID, cause=e) from e

    async def _call_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Guarded tool call wrapper using circuit breaker (+ optional AF-046 guardrails)."""
        if self.guardrails is not None:
            verdict = await self.guardrails.around_tool(
                self._guard_context(), {"name": tool_name, "args": args}
            )
            if getattr(verdict, "blocked", False):
                raise ToolError(
                    f"Guardrail blocked tool '{tool_name}': {getattr(verdict, 'reason', None)}",
                    agent_id=self.AGENT_ID,
                )
        try:
            return await self._tool_breaker.call(self.tools.call, tool_name=tool_name, args=args)
        except CircuitOpenError as e:
            e.agent_id = self.AGENT_ID
            raise e
        except Exception as e:
            raise ToolError(f"Tool call failed: {e}", agent_id=self.AGENT_ID, cause=e) from e

    @abstractmethod
    async def understand(self, input: TIn) -> dict[str, Any]:
        """Parse raw input into a structured intent."""
        ...

    @abstractmethod
    async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Decompose intent into steps."""
        ...

    @abstractmethod
    async def execute(self, plan: dict[str, Any]) -> TOut:
        """Execute plan and produce raw output."""
        ...

    @abstractmethod
    async def verify(self, output: TOut) -> dict[str, Any]:
        """Validate output before return."""
        ...

    @abstractmethod
    async def learn(self, trace: dict[str, Any]) -> None:
        """Emit run traces to LLMOps."""
        ...

    async def run(self, input: TIn) -> TOut:
        """Execute understand -> plan -> execute -> verify -> learn.

        Wraps each step, enforces SLA_SECONDS budget, maps raw exceptions, and emits trace.
        """
        run_id = None
        org_id = get_tenant_context()

        if isinstance(input, BaseModel):
            run_id = str(getattr(input, "run_id", "")) or None
            if not org_id:
                org_id = str(getattr(input, "organization_id", "")) or None
        elif isinstance(input, dict):
            run_id = str(input.get("run_id", "")) or None
            if not org_id:
                org_id = str(input.get("organization_id", "")) or None

        # Expose the run id to the guarded LLM/tool wrappers for lineage context.
        self._current_run_id = run_id

        trace: dict[str, Any] = {
            "agent_id": self.AGENT_ID,
            "run_id": run_id,
            "organization_id": org_id,
            "steps": [],
        }

        try:
            async with asyncio.timeout(self.SLA_SECONDS):
                # 1. Understand
                try:
                    intent = await self.understand(input)
                    trace["intent"] = intent
                except AgentError:
                    raise
                except Exception as e:
                    raise UnderstandError(
                        f"Understand phase failed: {e}",
                        agent_id=self.AGENT_ID,
                        run_id=run_id,
                        cause=e,
                    ) from e

                # 2. Plan
                try:
                    plan = await self.plan(intent)
                    trace["plan"] = plan
                except AgentError:
                    raise
                except Exception as e:
                    raise PlanError(
                        f"Plan phase failed: {e}",
                        agent_id=self.AGENT_ID,
                        run_id=run_id,
                        cause=e,
                    ) from e

                # 3. Execute
                try:
                    output = await self.execute(plan)
                    trace["output"] = output
                except AgentError:
                    raise
                except Exception as e:
                    raise ExecuteError(
                        f"Execute phase failed: {e}",
                        agent_id=self.AGENT_ID,
                        run_id=run_id,
                        cause=e,
                    ) from e

                # 4. Verify
                try:
                    verify_result = await self.verify(output)
                    trace["verify_result"] = verify_result
                except AgentError:
                    raise
                except Exception as e:
                    raise VerifyError(
                        f"Verify phase failed: {e}",
                        agent_id=self.AGENT_ID,
                        run_id=run_id,
                        cause=e,
                    ) from e

                return output

        except TimeoutError as e:
            raise SLAExceededError(
                f"Agent run exceeded SLA budget of {self.SLA_SECONDS} seconds",
                agent_id=self.AGENT_ID,
                run_id=run_id,
                cause=e,
            ) from e

        finally:
            # 5. Learn
            try:
                await self.learn(trace)
            except Exception as e:
                import logging

                logger = logging.getLogger("app.agents.base")
                logger.error(
                    f"Agent learn phase failed (non-fatal): {e}",
                    exc_info=True,
                    extra={"agent_id": self.AGENT_ID, "run_id": run_id},
                )
