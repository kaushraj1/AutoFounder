"""Shared fixtures for Reviewer Agent (AF-042) tests.

Provides a configurable fake LLM router, a stub UDAL with an object store, an
agent factory (MemorySaver checkpointer), and sample-state/repo builders. Tools
are monkeypatched per-test so the suite runs with no Docker / scanners / network.

``collect_ignore_glob`` keeps pytest from collecting the sample-repo fixtures
(which contain intentionally-broken example code) as real tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.agents._providers import JinjaPromptRegistry
from app.agents.reviewer.agent import ReviewerAgent
from app.agents.reviewer.registry import ReviewerToolRegistry
from app.agents.reviewer.schema import ReviewerState

collect_ignore_glob = ["fixtures/**"]

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_repos"


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeReviewerLLM:
    """Deterministic router. Tweak attributes per-test to steer the graph."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.judge_approved = True
        self.judge_scores = (85, 82, 80, 83)  # readability, maint, security, overall
        self.heal_patches: list[dict[str, str]] = []
        self.report = "# Code Review Report\n\nApproved."
        self.fail_task_class: str | None = None

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        self.calls.append((task_class, prompt))
        if self.fail_task_class == task_class:
            raise RuntimeError(f"FakeLLM forced failure on {task_class}")
        if task_class == "reviewer_judge":
            r, m, s, o = self.judge_scores
            return json.dumps(
                {
                    "readability": r,
                    "maintainability": m,
                    "security_posture": s,
                    "overall": o,
                    "approved": self.judge_approved,
                    "rationale": "fake",
                }
            )
        if task_class == "reviewer_triage":
            return json.dumps({"decision": "approved", "reason": "fake", "failures": []})
        if task_class == "reviewer_heal":
            return json.dumps({"patches": self.heal_patches})
        if task_class == "reviewer_report":
            return self.report
        return "{}"


class StubObjectStore:
    def __init__(self) -> None:
        self.uploads: list[str] = []

    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        self.uploads.append(path)
        return f"memory://{path}"


class StubUDAL:
    def __init__(self) -> None:
        self._store = StubObjectStore()

    def object(self) -> StubObjectStore:
        return self._store


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_llm() -> FakeReviewerLLM:
    return FakeReviewerLLM()


@pytest.fixture
def stub_udal() -> StubUDAL:
    return StubUDAL()


@pytest.fixture
def make_agent(fake_llm: FakeReviewerLLM, stub_udal: StubUDAL):
    """Factory: build a ReviewerAgent wired with fakes + an in-memory checkpointer."""

    def _make(llm: Any | None = None, udal: Any | None = None) -> ReviewerAgent:
        return ReviewerAgent(
            udal=udal or stub_udal,
            checkpointer=MemorySaver(),
            tool_registry=ReviewerToolRegistry(),
            prompt_registry=JinjaPromptRegistry(),
            llm_router=llm or fake_llm,
        )

    return _make


@pytest.fixture
def python_repo(tmp_path: Path) -> str:
    """A minimal Python-only repo (for ingest/language-detection)."""
    (tmp_path / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "calc.py").write_text("def sub(a, b):\n    return a - b\n", encoding="utf-8")
    return str(tmp_path)


@pytest.fixture
def fullstack_repo(tmp_path: Path) -> str:
    """A repo with both Python and TypeScript sources + a package.json."""
    (tmp_path / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "index.ts").write_text("export const x = 1;\n", encoding="utf-8")
    (tmp_path / "package.json").write_text('{"name": "demo"}\n', encoding="utf-8")
    return str(tmp_path)


def make_state(**overrides: Any) -> ReviewerState:
    """Build a ReviewerState with sensible defaults for unit tests."""
    base: dict[str, Any] = {
        "organization_id": "org-test",
        "repo_url": "https://github.com/acme/demo",
        "pr_number": 7,
        "branch": "main",
        "workdir": "/tmp/demo",
        "has_python": True,
        "has_typescript": False,
    }
    base.update(overrides)
    return ReviewerState(**base)
