"""Local BaseAgent stub for standalone development (AF-040).

This file lets ArchitectAgent subclass BaseAgent WITHOUT waiting for
Asit's AF-036. When AF-036 lands, replace this import in agent.py:

    # Before (standalone)
    from app.agents.architect.base_stub import BaseAgent

    # After (wired to platform)
    from app.agents.base import Agent as BaseAgent

Nothing else changes — all node logic, graph, and tests stay identical.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class Intent(BaseModel):
    summary: str
    metadata: dict[str, Any] = {}


class Plan(BaseModel):
    steps: list[str] = []


class VerifyResult(BaseModel):
    passed: bool
    issues: list[str] = []


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Minimal stand-in for Asit's AF-036 BaseAgent.

    Implements the five-method Understand → Plan → Execute → Verify → Learn
    loop so ArchitectAgent can inherit and override each method independently.
    """

    PILLAR: int = 0
    AGENT_ID: str = "base"
    SLA_SECONDS: int = 300

    @abstractmethod
    async def understand(self, input_state: InputT) -> Intent:
        """Parse raw input into a structured intent."""

    @abstractmethod
    async def plan(self, intent: Intent) -> Plan:
        """Decompose intent into an ordered plan."""

    @abstractmethod
    async def execute(self, plan: Plan) -> OutputT:
        """Execute the plan and return the agent output."""

    @abstractmethod
    async def verify(self, output: OutputT) -> VerifyResult:
        """Self-critique the output before returning it."""

    @abstractmethod
    async def learn(self, trace: dict[str, Any]) -> None:
        """Emit execution trace to the LLMOps learning loop."""
