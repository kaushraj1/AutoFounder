"""NoToolRegistry for Coder Agent.

CoderAgent generates code using only LLM calls — all context already
lives in ArchitectOutput gathered by the Architect Agent (AF-040).
This registry satisfies BaseAgent DI and raises loudly if _call_tool
is ever accidentally invoked.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import ToolRegistryProtocol


class NoToolRegistry(ToolRegistryProtocol):
    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            f"CoderAgent does not use external tools (attempted: '{tool_name}'). "
            "All inputs are sourced from ArchitectOutput."
        )
