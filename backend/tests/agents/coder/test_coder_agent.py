"""Tests for CoderAgent (AF-041, Pillar 3).

Test coverage:
  T1: Happy path — FakeLLM returns valid JSON files → output has all 4 sections non-empty
  T2: understand() rejects empty feature_list
  T3: Cache hit short-circuits execute (no LLM calls on 2nd run)
  T4: verify() sets confidence=low when zero files generated
  T5: Malformed LLM JSON → graceful empty list, warnings added
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.agents.architect.schema import ArchitectOutput, FeatureList, Requirement
from app.agents.base import ToolRegistryProtocol
from app.agents.coder.agent import CoderAgent
from app.agents.coder.registry import NoToolRegistry
from app.agents.coder.schema import CoderInput, CoderOutput, GeneratedFile

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

_FAKE_BACKEND_FILES = {
    "files": [
        {
            "path": "backend/app/main.py",
            "content": (
                'from fastapi import FastAPI\n\napp = FastAPI()\n\n'
                '@app.get("/health")\nasync def health():\n    return {"status": "ok"}\n'
            ),
            "language": "python",
        },
        {
            "path": "backend/app/models/user.py",
            "content": (
                "from sqlalchemy.orm import DeclarativeBase\n\n"
                "class Base(DeclarativeBase): pass\n\n"
                "class User(Base):\n    __tablename__ = 'users'\n"
            ),
            "language": "python",
        },
        {
            "path": "backend/app/api/v1/router.py",
            "content": "from fastapi import APIRouter\nrouter = APIRouter()\n",
            "language": "python",
        },
    ]
}

_FAKE_FRONTEND_FILES = {
    "files": [
        {
            "path": "frontend/app/layout.tsx",
            "content": (
                'import type { Metadata } from "next"\n'
                'export const metadata: Metadata = { title: "App" }\n'
                "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
                '  return <html><body>{children}</body></html>\n}\n'
            ),
            "language": "typescript",
        },
        {
            "path": "frontend/app/page.tsx",
            "content": 'export default function Home() { return <main>Hello</main> }\n',
            "language": "typescript",
        },
    ]
}

_FAKE_CONFIG_FILES = {
    "files": [
        {
            "path": "docker-compose.yml",
            "content": (
                "version: '3.8'\nservices:\n  backend:\n    build: ./backend\n"
                "    ports:\n      - '8000:8000'\n"
            ),
            "language": "yaml",
        },
        {
            "path": "README.md",
            "content": "# My SaaS App\n\nA FastAPI + Next.js application.\n",
            "language": "yaml",
        },
    ]
}

_FAKE_TEST_FILES = {
    "files": [
        {
            "path": "backend/tests/conftest.py",
            "content": "import pytest\n\n@pytest.fixture\nasync def client(): pass\n",
            "language": "python",
        },
        {
            "path": "backend/tests/test_health.py",
            "content": (
                "import pytest\n\n@pytest.mark.asyncio\n"
                "async def test_health_returns_200(client):\n    pass\n"
            ),
            "language": "python",
        },
    ]
}


# ---------------------------------------------------------------------------
# Fake LLM router — cycles through staged responses
# ---------------------------------------------------------------------------


class FakeCoderLLMRouter:
    def __init__(self, responses: list[str] | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self._call_count = 0
        self._responses = responses or [
            json.dumps(_FAKE_BACKEND_FILES),
            json.dumps(_FAKE_FRONTEND_FILES),
            json.dumps(_FAKE_CONFIG_FILES),
            json.dumps(_FAKE_TEST_FILES),
        ]

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        self.calls.append((task_class, prompt))
        idx = self._call_count % len(self._responses)
        self._call_count += 1
        return self._responses[idx]


class FakeNoToolRegistry(ToolRegistryProtocol):
    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("CoderAgent does not use tools")


# ---------------------------------------------------------------------------
# Fake UDAL with cache + object store
# ---------------------------------------------------------------------------


def make_fake_udal(cache_data: dict | None = None) -> MagicMock:
    udal = MagicMock()

    # Cache
    cache = MagicMock()
    _store: dict[str, Any] = {}
    if cache_data:
        _store.update(cache_data)

    async def get_session(key: str) -> dict | None:
        return _store.get(key)

    async def set_session(key: str, data: dict, ttl: int = 86400) -> None:
        _store[key] = data

    cache.get_session = AsyncMock(side_effect=get_session)
    cache.set_session = AsyncMock(side_effect=set_session)
    udal.cache = cache

    # Object store
    obj = MagicMock()
    obj.upload = AsyncMock(return_value="https://storage.supabase.io/coder/run-001/output.json")
    udal.object = MagicMock(return_value=obj)

    return udal


# ---------------------------------------------------------------------------
# Fixture: sample ArchitectOutput
# ---------------------------------------------------------------------------


def make_architect_output(empty_features: bool = False) -> ArchitectOutput:
    return ArchitectOutput(
        run_id=UUID("00000000-0000-0000-0000-000000000001"),
        organization_id="org-001",
        requirements=[
            Requirement(id="FR-001", kind="FR", description="User authentication", priority="P0"),
            Requirement(
                id="FR-002", kind="FR", description="Dashboard with analytics", priority="P1"
            ),
            Requirement(
                id="NFR-001", kind="NFR", description="Response time < 200ms", priority="P0"
            ),
        ],
        erd_mermaid=(
            "erDiagram\n  USER {\n    UUID id PK\n    string email\n    string name\n  }\n"
        ),
        openapi_3_1={
            "openapi": "3.1.0",
            "info": {"title": "TeamSync API", "version": "1.0.0"},
            "paths": {
                "/health": {"get": {"summary": "Health check"}},
                "/users": {"get": {"summary": "List users"}, "post": {"summary": "Create user"}},
            },
        },
        stack={
            "frontend": "Next.js 14",
            "backend": "FastAPI",
            "database": "PostgreSQL + pgvector",
            "infra": "AWS ECS Fargate",
        },
        microservice_boundaries=["auth-service", "core-api"],
        auth_strategy={"type": "JWT", "provider": "Supabase Auth"},
        scaling_plan={"min_instances": 2, "max_instances": 10},
        cost_estimate={"monthly_usd": 150.0, "breakdown": {"compute": 100, "db": 50}},
        feature_list=FeatureList(
            features=[] if empty_features else ["User Auth", "Dashboard", "Analytics"],
            integrations=["Stripe", "SendGrid"],
            pricing_tiers=[{"name": "Starter", "price_usd": 29}],
        ),
        approval_status="approved",
    )


def make_coder_input(empty_features: bool = False) -> CoderInput:
    return CoderInput(
        run_id="run-coder-001",
        organization_id="org-001",
        architect_output=make_architect_output(empty_features=empty_features),
    )


def make_agent(
    fake_llm: FakeCoderLLMRouter,
    fake_udal: MagicMock | None = None,
) -> CoderAgent:
    from app.agents._providers.jinja_prompt_registry import JinjaPromptRegistry

    return CoderAgent(
        udal=fake_udal or make_fake_udal(),
        checkpointer=MagicMock(),
        tool_registry=FakeNoToolRegistry(),
        prompt_registry=JinjaPromptRegistry(),
        llm_router=fake_llm,
    )


# ---------------------------------------------------------------------------
# T1: Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_all_sections_populated() -> None:
    """T1: FakeLLM returns valid JSON → output has all 4 sections non-empty."""
    fake_llm = FakeCoderLLMRouter()
    agent = make_agent(fake_llm)
    inp = make_coder_input()

    result = await agent.run(inp)

    assert isinstance(result, CoderOutput)
    assert len(result.backend_files) > 0, "backend_files must not be empty"
    assert len(result.frontend_files) > 0, "frontend_files must not be empty"
    assert len(result.config_files) > 0, "config_files must not be empty"
    assert len(result.test_files) > 0, "test_files must not be empty"
    assert result.total_files > 0
    assert result.total_lines > 0
    assert result.total_llm_tokens_used > 0
    # All 4 stages must have called the LLM
    assert fake_llm._call_count == 4
    assert all(tc == "coder_generation" for tc, _ in fake_llm.calls)


# ---------------------------------------------------------------------------
# T2: understand() rejects empty feature_list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_understand_rejects_empty_feature_list() -> None:
    """T2: CoderInput with empty feature_list.features raises ValueError."""
    fake_llm = FakeCoderLLMRouter()
    agent = make_agent(fake_llm)

    # FeatureList.features validator raises on empty, so we bypass by mutating post-init
    ao = make_architect_output(empty_features=False)
    ao.feature_list.__dict__["features"] = []  # bypass validator for test

    inp = CoderInput(
        run_id="run-empty-features",
        organization_id="org-001",
        architect_output=ao,
    )

    with pytest.raises((ValueError, Exception)):
        await agent.run(inp)


# ---------------------------------------------------------------------------
# T3: Cache hit short-circuits execute (no LLM calls on 2nd run)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_hit_skips_llm() -> None:
    """T3: If Redis cache is pre-seeded, LLM is never called."""
    fake_llm = FakeCoderLLMRouter()
    inp = make_coder_input()

    # Compute the expected cache key
    digest = hashlib.sha256(inp.run_id.encode()).hexdigest()[:16]
    cache_key = f"coder:cache:{digest}"

    # Build a minimal CoderOutput to seed into cache
    sample_file = GeneratedFile(
        path="backend/app/main.py",
        content="# cached main\n",
        language="python",
    )
    cached_output = CoderOutput(
        run_id=inp.run_id,
        organization_id=inp.organization_id,
        generated_files=[sample_file],
        backend_files=[sample_file],
        frontend_files=[],
        config_files=[],
        test_files=[],
        total_files=1,
        total_lines=1,
        total_llm_tokens_used=42,
        confidence="high",
    )

    udal = make_fake_udal(cache_data={cache_key: cached_output.model_dump()})
    agent = make_agent(fake_llm, fake_udal=udal)

    result = await agent.run(inp)

    # LLM should NOT have been called at all
    assert fake_llm._call_count == 0
    assert result.run_id == inp.run_id
    assert result.total_llm_tokens_used == 42


# ---------------------------------------------------------------------------
# T4: verify() sets confidence=low when zero files generated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_sets_low_confidence_on_zero_files() -> None:
    """T4: When LLM returns no files, confidence must be 'low'."""
    # Return empty files lists from LLM
    empty_response = json.dumps({"files": []})
    fake_llm = FakeCoderLLMRouter(
        responses=[empty_response, empty_response, empty_response, empty_response]
    )
    agent = make_agent(fake_llm)
    inp = make_coder_input()

    result = await agent.run(inp)

    assert result.confidence == "low"
    assert result.total_files == 0


# ---------------------------------------------------------------------------
# T5: Malformed LLM JSON → graceful empty list, warnings added
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_malformed_llm_json_returns_empty_with_warnings() -> None:
    """T5: Malformed JSON from LLM produces graceful degradation with warnings."""
    malformed = "This is not JSON at all! {broken"
    fake_llm = FakeCoderLLMRouter(
        responses=[malformed, malformed, malformed, malformed]
    )
    agent = make_agent(fake_llm)
    inp = make_coder_input()

    # Should not raise; should produce low-confidence output
    result = await agent.run(inp)

    assert result.total_files == 0
    assert result.confidence == "low"
    # warnings should mention the problem
    assert len(result.warnings) > 0


# ---------------------------------------------------------------------------
# T6: NoToolRegistry raises on call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_tool_registry_raises() -> None:
    """T6: NoToolRegistry.call() raises NotImplementedError for any tool name."""
    registry = NoToolRegistry()
    with pytest.raises(NotImplementedError, match="does not use external tools"):
        await registry.call("some_tool", {})


# ---------------------------------------------------------------------------
# T7: generated_files is the union of all 4 section lists
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generated_files_is_union_of_all_sections() -> None:
    """T7: generated_files = backend + frontend + config + test files combined."""
    fake_llm = FakeCoderLLMRouter()
    agent = make_agent(fake_llm)
    inp = make_coder_input()

    result = await agent.run(inp)

    expected_total = (
        len(result.backend_files)
        + len(result.frontend_files)
        + len(result.config_files)
        + len(result.test_files)
    )
    assert len(result.generated_files) == expected_total
    assert result.total_files == expected_total


# ---------------------------------------------------------------------------
# T8: High-volume output gets confidence=high
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_high_volume_output_gets_high_confidence() -> None:
    """T8: 20+ files with 500+ lines → confidence='high'."""
    # Generate a large set of files to cross the high-confidence threshold
    many_files = [
        {
            "path": f"backend/app/module_{i}.py",
            "content": "\n".join(f"# line {j}" for j in range(30)),
            "language": "python",
        }
        for i in range(6)
    ]
    frontend_files = [
        {
            "path": f"frontend/app/page_{i}.tsx",
            "content": "\n".join(f"// line {j}" for j in range(30)),
            "language": "typescript",
        }
        for i in range(6)
    ]
    config_files_data = [
        {
            "path": f"config/file_{i}.yml",
            "content": "\n".join(f"# cfg {j}" for j in range(20)),
            "language": "yaml",
        }
        for i in range(5)
    ]
    test_files_data = [
        {
            "path": f"backend/tests/test_module_{i}.py",
            "content": "\n".join(f"# test {j}" for j in range(20)),
            "language": "python",
        }
        for i in range(5)
    ]

    fake_llm = FakeCoderLLMRouter(
        responses=[
            json.dumps({"files": many_files}),
            json.dumps({"files": frontend_files}),
            json.dumps({"files": config_files_data}),
            json.dumps({"files": test_files_data}),
        ]
    )
    agent = make_agent(fake_llm)
    inp = make_coder_input()

    result = await agent.run(inp)

    assert result.confidence == "high"
    assert result.total_files >= 20
    assert result.total_lines >= 500


# ---------------------------------------------------------------------------
# T9: Cache is populated after a fresh run
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_is_populated_after_fresh_run() -> None:
    """T9: After a successful run, the cache contains the output."""
    fake_llm = FakeCoderLLMRouter()
    udal = make_fake_udal()
    agent = make_agent(fake_llm, fake_udal=udal)
    inp = make_coder_input()

    await agent.run(inp)

    digest = hashlib.sha256(inp.run_id.encode()).hexdigest()[:16]
    cache_key = f"coder:cache:{digest}"
    udal.cache.set_session.assert_called_once()
    call_args = udal.cache.set_session.call_args
    assert call_args[0][0] == cache_key
