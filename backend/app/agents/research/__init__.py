"""Research agent (Pillar 1) — market/user/competitor/tech research."""

from app.agents.base import (
    Agent,
    AgentInput,
    AgentOutput,
    ExecutionTrace,
    Intent,
    Plan,
    StepEvent,
    VerifyResult,
)

_TODO = "ResearchAgent logic lands in Phase 1 Sprint 1"


class ResearchAgent(Agent):
    """Gathers and synthesizes external research to support validation."""

    id = "research.v1"
    capabilities = ["planning", "reasoning", "tool_use", "memory"]

    async def understand(self, agent_input: AgentInput) -> Intent:
        raise NotImplementedError(_TODO)

    async def plan(self, intent: Intent) -> Plan:
        raise NotImplementedError(_TODO)

    async def execute(self, plan: Plan) -> list[StepEvent]:
        raise NotImplementedError(_TODO)

    async def verify(self, output: AgentOutput) -> VerifyResult:
        raise NotImplementedError(_TODO)

    async def learn(self, trace: ExecutionTrace) -> None:
        raise NotImplementedError(_TODO)
