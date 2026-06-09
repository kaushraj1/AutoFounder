"""Tool Registry error hierarchy (AF-047).

Kept independent of ``app.agents.base.AgentError`` to avoid an import cycle
(``base`` -> ``tools`` -> ``base``). ``BaseAgent._call_tool`` already wraps any
exception raised here into a typed ``ToolError`` with agent/run context.
"""

from __future__ import annotations

from typing import Any


class ToolRegistryError(Exception):
    """Base class for tool registry failures. Carries structured detail."""

    def __init__(self, message: str, *, tool: str | None = None, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.tool = tool
        self.detail = detail


class ToolNotFoundError(ToolRegistryError):
    """Requested tool is not registered (fails the allow-list)."""


class ToolValidationError(ToolRegistryError):
    """Provided args do not satisfy the tool's ``args_schema``."""


class ToolNotAllowedError(ToolRegistryError):
    """Caller lacks the auth scope the tool requires."""


class ToolRateLimitError(ToolRegistryError):
    """Per-tenant rate limit for this tool was exceeded."""
