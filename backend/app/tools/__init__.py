"""Shared platform Tool Registry (AF-047).

The single allow-list of tools agents may invoke. Import the singleton via
``get_tool_registry()``; the Execution Guard (AF-046 stage 4) reads the same
registry to enforce schema, scope, rate limit, and cost cap.
"""

from app.tools.errors import (
    ToolNotAllowedError,
    ToolNotFoundError,
    ToolRateLimitError,
    ToolRegistryError,
    ToolValidationError,
)
from app.tools.registry import ToolRegistry, get_tool_registry
from app.tools.schema import CostClass, ToolFn, ToolSpec

__all__ = [
    "CostClass",
    "ToolFn",
    "ToolSpec",
    "ToolRegistry",
    "get_tool_registry",
    "ToolRegistryError",
    "ToolNotFoundError",
    "ToolValidationError",
    "ToolNotAllowedError",
    "ToolRateLimitError",
]
