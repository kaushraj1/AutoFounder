"""NoToolRegistry for LLMOps Agent.

LLMOps Agent performs analysis via LLM calls only — it reads trace data
passed directly in LLMOpsInput rather than calling external tools.
This registry satisfies BaseAgent DI and raises loudly if _call_tool
is ever accidentally invoked.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import ToolRegistryProtocol


class NoToolRegistry(ToolRegistryProtocol):
    """LLMOpsAgent performs analysis via LLM calls only."""

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            f"LLMOpsAgent does not use external tools (attempted: '{tool_name}'). "
            "All trace data is sourced from LLMOpsInput."
        )
