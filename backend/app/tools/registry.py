"""``ToolRegistry`` singleton (AF-047).

The shared, platform-level allow-list of tools every agent may invoke. Each
pillar registers its own tools into the one registry; the Execution Guard
(AF-046 stage 4) reads the same registry to enforce schema, scope, rate limit
and cost cap before a call runs.

Contract: ``call(tool_name, args)`` satisfies ``ToolRegistryProtocol`` from
``app.agents.base`` so a ``ToolRegistry`` is directly injectable into any
``BaseAgent``.

Validation supports two ``args_schema`` shapes:
  * a Pydantic ``BaseModel`` subclass  -> ``model_validate`` (full coercion)
  * a JSON-schema ``dict``             -> lightweight ``required`` + type check

Usage::

    registry = get_tool_registry()
    registry.register("aws_pricing", _aws_pricing, args_schema=PricingArgs,
                      auth_scope="engineering", cost_class=CostClass.LOW)
    result = await registry.call("aws_pricing", {"service": "ecs"})
"""

from __future__ import annotations

import inspect
import logging
from typing import Any

from pydantic import BaseModel, ValidationError

from app.tools.errors import (
    ToolNotAllowedError,
    ToolNotFoundError,
    ToolValidationError,
)
from app.tools.schema import CostClass, ToolFn, ToolSpec

logger = logging.getLogger(__name__)

# JSON-schema type name -> Python types accepted for the lightweight validator.
_JSON_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


class ToolRegistry:
    """In-process registry of callable tools, keyed by unique name.

    Thread-safety: registration happens at import/startup (single-threaded);
    ``call`` is read-only against the map and safe under asyncio concurrency.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        fn: ToolFn,
        *,
        args_schema: type | dict[str, Any] | None = None,
        auth_scope: str | None = None,
        cost_class: CostClass = CostClass.FREE,
        rate_limit_per_min: int | None = None,
        description: str = "",
        tags: list[str] | None = None,
        replace: bool = False,
    ) -> ToolSpec:
        """Register a tool. Raises if ``name`` already exists and ``replace`` is False."""
        if not name or not name.strip():
            raise ValueError("Tool name must be a non-empty string")
        if name in self._tools and not replace:
            raise ValueError(f"Tool '{name}' is already registered (pass replace=True to override)")

        spec = ToolSpec(
            name=name,
            fn=fn,
            args_schema=args_schema,
            auth_scope=auth_scope,
            cost_class=cost_class,
            rate_limit_per_min=rate_limit_per_min,
            description=description,
            tags=list(tags) if tags else [],
        )
        self._tools[name] = spec
        logger.debug("tool_registered name=%s scope=%s cost=%s", name, auth_scope, cost_class.value)
        return spec

    def unregister(self, name: str) -> None:
        """Remove a tool if present (no error if absent)."""
        self._tools.pop(name, None)

    def clear(self) -> None:
        """Drop all registered tools. Primarily for test isolation."""
        self._tools.clear()

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, name: str) -> ToolSpec:
        """Return the spec for ``name`` or raise ``ToolNotFoundError``."""
        spec = self._tools.get(name)
        if spec is None:
            raise ToolNotFoundError(f"Tool '{name}' is not registered", tool=name)
        return spec

    def has(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs(self) -> list[ToolSpec]:
        return list(self._tools.values())

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_args(self, spec: ToolSpec, args: dict[str, Any]) -> dict[str, Any]:
        """Validate ``args`` against the spec schema; returns coerced args.

        Raises ``ToolValidationError`` on any mismatch. ``None`` schema = passthrough.
        """
        schema = spec.args_schema
        if schema is None:
            return args
        if not isinstance(args, dict):
            raise ToolValidationError(
                f"Tool '{spec.name}' args must be a dict, got {type(args).__name__}",
                tool=spec.name,
            )

        # Pydantic model schema -> full validation + coercion.
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                return schema.model_validate(args).model_dump()
            except ValidationError as exc:
                raise ToolValidationError(
                    f"Tool '{spec.name}' args failed schema validation",
                    tool=spec.name,
                    detail=exc.errors(),
                ) from exc

        # JSON-schema dict -> lightweight required + type check.
        if isinstance(schema, dict):
            self._validate_json_schema(spec.name, schema, args)
            return args

        raise ToolValidationError(
            f"Tool '{spec.name}' has an unsupported args_schema type", tool=spec.name
        )

    @staticmethod
    def _validate_json_schema(name: str, schema: dict[str, Any], args: dict[str, Any]) -> None:
        required = schema.get("required", [])
        missing = [key for key in required if key not in args]
        if missing:
            raise ToolValidationError(
                f"Tool '{name}' missing required args: {', '.join(missing)}",
                tool=name,
                detail={"missing": missing},
            )
        properties: dict[str, Any] = schema.get("properties", {})
        for key, value in args.items():
            prop = properties.get(key)
            if not prop:
                continue
            expected = prop.get("type")
            allowed = _JSON_TYPES.get(expected) if expected else None
            if allowed is None:
                continue
            # bool is a subclass of int — reject it explicitly for "integer"/"number".
            if expected in ("integer", "number") and isinstance(value, bool):
                raise ToolValidationError(
                    f"Tool '{name}' arg '{key}' expected {expected}, got boolean",
                    tool=name,
                )
            if not isinstance(value, allowed):
                raise ToolValidationError(
                    f"Tool '{name}' arg '{key}' expected {expected}, got {type(value).__name__}",
                    tool=name,
                )

    # ------------------------------------------------------------------
    # Invocation (ToolRegistryProtocol contract)
    # ------------------------------------------------------------------

    async def call(
        self,
        tool_name: str,
        args: dict[str, Any],
        *,
        granted_scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Validate then invoke a registered tool, returning its dict result.

        ``granted_scopes`` (the caller's authorised scopes) is enforced as
        defense-in-depth when provided; pass ``None`` to skip the scope check
        (the Execution Guard remains the primary policy gate).
        """
        spec = self.get(tool_name)
        validated = self.validate_args(spec, args)

        if (
            granted_scopes is not None
            and spec.auth_scope is not None
            and spec.auth_scope not in granted_scopes
        ):
            raise ToolNotAllowedError(
                f"Tool '{tool_name}' requires scope '{spec.auth_scope}'",
                tool=tool_name,
                detail={"required": spec.auth_scope, "granted": granted_scopes},
            )

        result = spec.fn(**validated)
        if inspect.isawaitable(result):
            result = await result
        if not isinstance(result, dict):
            raise ToolValidationError(
                f"Tool '{tool_name}' must return a dict, got {type(result).__name__}",
                tool=tool_name,
            )
        return result


# Module-level singleton — the one shared registry every pillar registers into.
_REGISTRY = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Return the process-wide shared ``ToolRegistry`` singleton."""
    return _REGISTRY
