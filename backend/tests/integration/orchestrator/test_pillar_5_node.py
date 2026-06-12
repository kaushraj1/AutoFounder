"""Integration tests for orchestrator.nodes.run_pillar_5.

Drives the orchestrator's Pillar 5 node with a real-shaped CoderOutput +
ReviewerOutput so the DevOpsAgent runs end-to-end via the LangGraph subgraph.

Heavy dependencies are stubbed:
  * SessionLocal -> in-memory no-op session
  * UDAL        -> ignores principal/session/redis
  * GeminiRouter / DualCheckpointer -> instantiated but never called by the
    scaffold tools

The test also exercises both spend-gate paths:
  * Auto-approve (cost <= settings.devops_spend_gate_cap_usd)
  * Redis polling (cost > cap, decision pre-written to fakeredis)
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import fakeredis.aioredis
import pytest

from app.agents.devops.schema import DeployStatus
from app.agents.devops.tests._fakes import FakeDevOpsLLMRouter
from app.core.config import get_settings

FIXTURE = (
    Path(__file__).resolve().parents[4]
    / ".claude"
    / "specs"
    / "pillar5-dummy-input.json"
)


class _StubSession:
    async def __aenter__(self) -> "_StubSession":
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def execute(self, *a: Any, **k: Any) -> Any:  # pragma: no cover
        return None

    async def commit(self) -> None:  # pragma: no cover
        return None


def _stub_session_factory(*a: Any, **k: Any) -> _StubSession:
    return _StubSession()


class _StubUDAL:
    def __init__(self, *, principal: Any, session: Any, redis: Any = None) -> None:
        self.principal = principal


class _StubGeminiRouter:
    def __init__(self, *a: Any, **k: Any) -> None:
        self._fake = FakeDevOpsLLMRouter()

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        return await self._fake.complete(task_class=task_class, prompt=prompt, **kw)


def _load_code_output() -> dict[str, Any]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # Mark non-stub so run_pillar_5's gate falls through to the real path.
    payload.pop("stub", None)
    payload.setdefault("repo_url", payload.get("github_repo_html_url", ""))
    return payload


def _build_run_state(
    code_output: dict[str, Any], review_output: dict[str, Any]
) -> dict[str, Any]:
    return {
        "run_id": str(uuid4()),
        "organization_id": "tenant-acme-saas-a1b2c3d4",
        "workspace_id": "ws-acme",
        "idea_text": code_output.get("idea_normalised", ""),
        "idea_meta": {},
        "status": "running",
        "current_pillar": 4,
        "current_node": "run_pillar_4",
        "retry_count": 0,
        "strategy_output": {"stub": False},
        "architecture_output": {"stub": False},
        "code_output": code_output,
        "review_output": review_output,
        "deployment_output": None,
        "marketing_output": None,
        "llmops_output": None,
        "active_gate_id": None,
        "gate_decision": None,
        "step_events": [],
        "error": None,
        "total_tokens_used": 0,
        "cost_usd_cents": 0,
    }


@pytest.fixture
def patched_pillar_5(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Patch heavy deps used by run_pillar_5 and return the patched module."""
    if not FIXTURE.exists():
        pytest.skip(f"Fixture {FIXTURE} not present")

    from langgraph.checkpoint.memory import MemorySaver

    # Patch the symbols at their definition sites so the run_pillar_5
    # local imports resolve to the stubs.
    import app.db.session as session_mod
    import app.db.udal as udal_mod
    import app.agents._providers as providers_mod
    import app.orchestrator.checkpointer as checkpointer_mod

    monkeypatch.setattr(session_mod, "SessionLocal", _stub_session_factory)
    monkeypatch.setattr(udal_mod, "UDAL", _StubUDAL)
    monkeypatch.setattr(providers_mod, "GeminiRouter", _StubGeminiRouter)
    # Replace the SQL+Redis checkpointer with an in-memory one so we don't
    # have to fake SQLAlchemy Result objects in the stub session.
    monkeypatch.setattr(
        checkpointer_mod,
        "DualCheckpointer",
        lambda *a, **k: MemorySaver(),
    )
    # Force DevOps tool wrappers into scaffold mode so the test never
    # hits AWS or PyGithub even if creds happen to be present in env.
    monkeypatch.setattr(get_settings(), "devops_tools_mode", "scaffold")
    return importlib.import_module("app.orchestrator.nodes")


async def test_run_pillar_5_skips_when_upstream_is_stub(
    patched_pillar_5: Any,
) -> None:
    state = _build_run_state(
        code_output={"stub": True},
        review_output={"stub": True},
    )

    result = await patched_pillar_5.run_pillar_5(state)

    assert result["deployment_output"]["stub"] is True
    assert result["deployment_output"]["deploy_url"] is None


async def test_run_pillar_5_happy_path_auto_approve(
    patched_pillar_5: Any,
) -> None:
    """Cost is under the cap → hitl_spend_gate auto-approves, full deploy runs."""
    code_output = _load_code_output()
    # Single small service keeps the computed monthly cost under the $150 cap
    # so the spend gate auto-approves without needing a founder decision.
    code_output["services"] = [
        {
            "name": "api-gateway",
            "image_uri": code_output["services"][0]["image_uri"],
            "port": 8000,
            "replicas_baseline": 1,
            "health_check_path": "/health",
            "env_secret_refs": [],
        }
    ]

    review_output = {
        "stub": False,
        "coverage": 0.84,
        "issues": [],
        "cycles": 1,
    }

    state = _build_run_state(code_output, review_output)
    result = await patched_pillar_5.run_pillar_5(state)

    assert result.get("status") != "failed", result.get("error")
    out = result["deployment_output"]
    assert out.get("stub") is not True
    assert out["live_url"], "configure_dns_ssl should populate live_url"
    assert out["smoke_passed"] is True
    assert out["deploy_status"] == str(DeployStatus.HEALTHY)
    assert out["monthly_cost_usd"] > 0

    full = out["full_state"]
    # Foundation VPC was injected from settings, not the placeholder.
    assert full["vpc_config"]["vpc_id"].startswith("vpc-")
    assert len(full["vpc_config"]["private_subnet_ids"]) >= 2
    assert full["approval_status"] == "approved"
    assert "Auto-approved" in (full.get("approval_comment") or "")


async def test_run_pillar_5_redis_polling_approval(
    patched_pillar_5: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cost exceeds the cap → spend gate polls Redis and finds 'approved'."""
    # Tight polling so the test completes quickly.
    settings = get_settings()
    monkeypatch.setattr(settings, "devops_hitl_poll_interval_seconds", 0.01)
    monkeypatch.setattr(settings, "devops_hitl_timeout_seconds", 1.0)

    code_output = _load_code_output()
    code_output["estimated_monthly_cost_usd"] = 500.0  # > $150 cap

    review_output = {"stub": False, "coverage": 0.84, "issues": [], "cycles": 1}

    state = _build_run_state(code_output, review_output)

    # Wire a fake Redis into both the spend gate and the orchestrator node.
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await fake_redis.set(
        f"hitl:devops:spend:{state['run_id']}", "approved"
    )

    hitl_module = importlib.import_module(
        "app.agents.devops.nodes.hitl_spend_gate"
    )
    monkeypatch.setattr(hitl_module, "_get_redis_client", lambda: fake_redis)

    import app.db.redis_pool as redis_pool

    monkeypatch.setattr(redis_pool, "get_redis", lambda: fake_redis)

    result = await patched_pillar_5.run_pillar_5(state)

    assert result.get("status") != "failed", result.get("error")
    out = result["deployment_output"]
    assert out["live_url"], "deploy should have completed after Redis approval"
    assert out["smoke_passed"] is True
    full = out["full_state"]
    assert full["approval_status"] == "approved"
    assert "Founder approved" in (full.get("approval_comment") or "")
