"""NoToolRegistry for Product Planner Agent.

Product Planner makes zero external tool calls — all market data already
lives in StrategyOutput gathered by Research Agent (AF-038).
This registry satisfies BaseAgent DI and raises loudly if _call_tool
is ever accidentally invoked.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import ToolRegistryProtocol


class NoToolRegistry(ToolRegistryProtocol):
    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            f"ProductPlannerAgent does not use external tools (attempted: '{tool_name}'). "
            "All inputs are sourced from StrategyOutput."
        )
