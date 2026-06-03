"""Strategy & Ideation agent (Pillar 1)."""

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

_TODO = "StrategyAgent logic lands in Phase 1 Sprint 1"


class StrategyAgent(Agent):
    """Owns end-to-end idea validation: market sizing, competitors, viability, pivots."""

    id = "strategy.v1"
    capabilities = ["planning", "reasoning", "tool_use", "memory", "self_learning"]

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
