"""Unit tests for the AF-047 Tool Registry."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.tools import (
    CostClass,
    ToolNotAllowedError,
    ToolNotFoundError,
    ToolRegistry,
    ToolValidationError,
    get_tool_registry,
)


class PricingArgs(BaseModel):
    service: str
    region: str = "us-east-1"


def _echo(**kwargs: object) -> dict[str, object]:
    return {"echo": kwargs}


async def _aecho(**kwargs: object) -> dict[str, object]:
    return {"aecho": kwargs}


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry()


def test_register_and_get(registry: ToolRegistry) -> None:
    registry.register("echo", _echo, cost_class=CostClass.LOW, auth_scope="research")
    spec = registry.get("echo")
    assert spec.name == "echo"
    assert spec.cost_class is CostClass.LOW
    assert spec.auth_scope == "research"
    assert registry.has("echo")
    assert registry.names() == ["echo"]


def test_duplicate_registration_rejected(registry: ToolRegistry) -> None:
    registry.register("echo", _echo)
    with pytest.raises(ValueError, match="already registered"):
        registry.register("echo", _echo)
    # replace=True overrides.
    registry.register("echo", _aecho, replace=True)
    assert registry.get("echo").fn is _aecho


def test_get_missing_raises(registry: ToolRegistry) -> None:
    with pytest.raises(ToolNotFoundError):
        registry.get("nope")


def test_empty_name_rejected(registry: ToolRegistry) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        registry.register("  ", _echo)


async def test_call_sync_tool(registry: ToolRegistry) -> None:
    registry.register("echo", _echo)
    result = await registry.call("echo", {"a": 1})
    assert result == {"echo": {"a": 1}}


async def test_call_async_tool(registry: ToolRegistry) -> None:
    registry.register("aecho", _aecho)
    result = await registry.call("aecho", {"b": 2})
    assert result == {"aecho": {"b": 2}}


async def test_call_unknown_tool_raises(registry: ToolRegistry) -> None:
    with pytest.raises(ToolNotFoundError):
        await registry.call("ghost", {})


async def test_pydantic_schema_validation_and_coercion(registry: ToolRegistry) -> None:
    registry.register("price", _echo, args_schema=PricingArgs)
    # Defaults filled, valid input.
    result = await registry.call("price", {"service": "ecs"})
    assert result["echo"]["service"] == "ecs"
    assert result["echo"]["region"] == "us-east-1"
    # Missing required field.
    with pytest.raises(ToolValidationError):
        await registry.call("price", {"region": "eu"})


async def test_json_schema_validation(registry: ToolRegistry) -> None:
    schema = {
        "required": ["query"],
        "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
    }
    registry.register("search", _echo, args_schema=schema)
    assert await registry.call("search", {"query": "ai", "limit": 5})
    with pytest.raises(ToolValidationError, match="missing required"):
        await registry.call("search", {"limit": 5})
    with pytest.raises(ToolValidationError, match="expected integer"):
        await registry.call("search", {"query": "ai", "limit": "five"})


async def test_json_schema_rejects_bool_as_integer(registry: ToolRegistry) -> None:
    schema = {"required": ["n"], "properties": {"n": {"type": "integer"}}}
    registry.register("count", _echo, args_schema=schema)
    with pytest.raises(ToolValidationError, match="boolean"):
        await registry.call("count", {"n": True})


async def test_auth_scope_enforced_when_scopes_given(registry: ToolRegistry) -> None:
    registry.register("deploy", _echo, auth_scope="engineering")
    with pytest.raises(ToolNotAllowedError):
        await registry.call("deploy", {}, granted_scopes=["marketing"])
    # Granted scope allows.
    assert await registry.call("deploy", {}, granted_scopes=["engineering"])
    # No scopes context => skip enforcement (execution guard is the primary gate).
    assert await registry.call("deploy", {})


async def test_non_dict_return_rejected(registry: ToolRegistry) -> None:
    registry.register("bad", lambda **_: "not a dict")
    with pytest.raises(ToolValidationError, match="must return a dict"):
        await registry.call("bad", {})


def test_singleton_is_shared() -> None:
    assert get_tool_registry() is get_tool_registry()
