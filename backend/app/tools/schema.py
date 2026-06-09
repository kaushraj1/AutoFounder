"""Tool Registry data models (AF-047).

Defines the typed handle for every tool the platform exposes to agents: its
callable, JSON-schema arguments, required auth scope, cost class, and rate
limit. These map 1:1 to the ``platform.tool_registry`` table
(``name``, ``args_schema`` JSONB, ``auth_scope``, ``cost_class``) so a registered
tool can be persisted and reloaded.

The registry is the single allow-list the Execution Guard (AF-046 stage 4)
reads to decide schema validity, scope, rate limit, and cost cap.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# A tool is any callable returning a dict (sync or async). The registry awaits
# coroutines and wraps plain returns, so both shapes are accepted.
ToolFn = Callable[..., Awaitable[dict[str, Any]]] | Callable[..., dict[str, Any]]


class CostClass(StrEnum):
    """Coarse per-call cost bucket used by the Execution Guard cost cap.

    Estimates are intentionally conservative upper bounds (USD) — the guard
    accumulates them per tenant and blocks once the configured cap is crossed.
    """

    FREE = "free"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def estimated_usd(self) -> float:
        """Conservative per-call cost estimate in USD for cap accounting."""
        return _COST_ESTIMATES[self]


_COST_ESTIMATES: dict[CostClass, float] = {
    CostClass.FREE: 0.0,
    CostClass.LOW: 0.002,
    CostClass.MEDIUM: 0.02,
    CostClass.HIGH: 0.20,
}


@dataclass(slots=True)
class ToolSpec:
    """A registered tool: its handle plus the metadata guards enforce.

    ``args_schema`` accepts either a Pydantic model class (validated via
    ``model_validate``) or a lightweight JSON-schema ``dict`` (``required`` +
    ``properties[].type`` checked). ``None`` means no argument validation.
    """

    name: str
    fn: ToolFn
    args_schema: type | dict[str, Any] | None = None
    auth_scope: str | None = None
    cost_class: CostClass = CostClass.FREE
    rate_limit_per_min: int | None = None
    description: str = ""
    tags: list[str] = field(default_factory=list)

    def to_row(self) -> dict[str, Any]:
        """Serialise the persistable subset for ``platform.tool_registry``."""
        schema: dict[str, Any] | None
        if isinstance(self.args_schema, dict):
            schema = self.args_schema
        elif self.args_schema is not None and hasattr(self.args_schema, "model_json_schema"):
            schema = self.args_schema.model_json_schema()
        else:
            schema = None
        return {
            "name": self.name,
            "args_schema": schema,
            "auth_scope": self.auth_scope,
            "cost_class": self.cost_class.value,
            "rate_limit_per_min": self.rate_limit_per_min,
            "description": self.description,
        }
