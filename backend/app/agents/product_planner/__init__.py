"""Product Planner agent (Pillar 1.5) — PRDs, roadmaps, requirements, user stories."""

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

_TODO = "ProductPlannerAgent logic lands in Phase 1 Sprint 1"


class ProductPlannerAgent(Agent):
    """Turns a validated idea into PRDs, roadmaps, and user stories."""

    id = "product_planner.v1"
    capabilities = ["planning", "reasoning", "memory"]

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
