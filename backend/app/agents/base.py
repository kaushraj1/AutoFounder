"""Agent contract (CLAUDE.md §7.3).

Every specialized agent implements the same five-method loop:
``Understand -> Plan -> Execute -> Verify -> Learn``.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


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
    """Base class for all specialized agents."""

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
