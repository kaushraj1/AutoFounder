"""Integration — drive the full Reviewer graph through ReviewerAgent.run().

Gate tools are monkeypatched (no Docker / scanners / real pytest), the LLM is the
deterministic FakeReviewerLLM, and persistence is the StubUDAL. These tests
exercise the real graph wiring, routers, triage decisions, and self-heal loop.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.agents.base import AgentError
from app.agents.reviewer.schema import (
    MAX_HEAL_CYCLES,
    GateStatus,
    OWASPCategory,
    ReviewDecision,
    ReviewerInput,
    SecurityFinding,
    SeverityLevel,
    SonarMetrics,
    TestFailure,
    TestSuiteResult,
)
from app.agents.reviewer.tools import (
    bandit,
    eslint,
    gitleaks,
    jest,
    playwright,
    pytest_runner,
    python_lint,
    semgrep,
    snyk,
    sonarqube,
    trivy,
)


def _patch_gates(
    mp: pytest.MonkeyPatch,
    *,
    lint: list | None = None,
    unit: Any = None,
    security: list | None = None,
    sonar: SonarMetrics | None = None,
    unit_factory: Any = None,
) -> None:
    """Replace all gate tools with controlled, deterministic results."""

    async def lint_run(sandbox: Any) -> list:
        return list(lint or [])

    async def unit_run(sandbox: Any) -> TestSuiteResult:
        if unit_factory is not None:
            return unit_factory()
        return unit or TestSuiteResult(runner="pytest", status=GateStatus.SKIPPED)

    async def skipped_unit(sandbox: Any) -> TestSuiteResult:
        return TestSuiteResult(runner="jest", status=GateStatus.SKIPPED)

    async def skipped_e2e(sandbox: Any) -> TestSuiteResult:
        return TestSuiteResult(runner="playwright", status=GateStatus.SKIPPED)

    async def trivy_run(sandbox: Any) -> list:
        return list(security or [])

    async def empty(sandbox: Any, **kw: Any) -> list:
        return []

    async def sonar_run(sandbox: Any, **kw: Any) -> SonarMetrics | None:
        return sonar

    mp.setattr(python_lint, "run", lint_run)
    mp.setattr(eslint, "run", lint_run)
    mp.setattr(pytest_runner, "run", unit_run)
    mp.setattr(jest, "run", skipped_unit)
    mp.setattr(playwright, "run", skipped_e2e)
    mp.setattr(trivy, "run", trivy_run)
    mp.setattr(semgrep, "run", empty)
    mp.setattr(gitleaks, "run", empty)
    mp.setattr(bandit, "run", empty)
    mp.setattr(snyk, "run", empty)
    mp.setattr(sonarqube, "run", sonar_run)


def _input(repo: str) -> ReviewerInput:
    return ReviewerInput(organization_id="org-int", repo_url="local", local_path=repo)


def _passed(coverage: float, **kw: Any) -> TestSuiteResult:
    return TestSuiteResult(runner="pytest", status=GateStatus.PASSED, coverage_pct=coverage, **kw)


async def test_happy_path_approves(make_agent, fake_llm, python_repo, monkeypatch) -> None:
    _patch_gates(monkeypatch, lint=[], unit=_passed(92.0, passed=10))
    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.APPROVED
    assert state.is_approved is True
    assert state.heal_cycle == 0
    assert state.review_report_markdown
    assert state.review_report_uri == f"memory://reviews/org-int/{state.run_id}/report.md"


async def test_self_heal_one_cycle_then_approves(
    make_agent, fake_llm, python_repo, monkeypatch
) -> None:
    calls = {"n": 0}

    def unit_factory() -> TestSuiteResult:
        calls["n"] += 1
        if calls["n"] == 1:
            return TestSuiteResult(
                runner="pytest",
                status=GateStatus.FAILED,
                failed=1,
                coverage_pct=90.0,
                failures=[TestFailure(test_id="test_add", message="assert 3 == 4")],
            )
        return _passed(90.0, passed=5)

    _patch_gates(monkeypatch, unit_factory=unit_factory)
    # Healer returns a source-file patch; apply is mocked to avoid disk writes.
    fake_llm.heal_patches = [{"file_path": "app.py", "new_content": "x", "rationale": "fix"}]
    from app.agents.reviewer.tools import github

    async def fake_apply(sandbox: Any, files: dict, **kw: Any) -> list:
        return list(files.keys())

    monkeypatch.setattr(github, "apply_patches", fake_apply)

    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.APPROVED
    assert state.heal_cycle == 1
    assert len(state.heal_history) == 1
    assert state.heal_history[0].files_patched == ["app.py"]


async def test_owasp_critical_escalates(make_agent, fake_llm, python_repo, monkeypatch) -> None:
    finding = SecurityFinding(
        tool="semgrep",
        severity=SeverityLevel.CRITICAL,
        rule_id="sqli",
        file_path="app.py",
        message="SQL injection",
        owasp_category=OWASPCategory.A03_INJECTION,
    )
    _patch_gates(monkeypatch, unit=_passed(95.0), security=[finding])
    # Verify the error sink tears the sandbox down on the escalation path.
    from app.agents.reviewer.tools import sandbox as sandbox_tool

    torn = {"called": False}

    async def fake_teardown(sandbox: Any) -> None:
        torn["called"] = True

    monkeypatch.setattr(sandbox_tool, "teardown", fake_teardown)

    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.ESCALATE
    assert state.is_approved is False
    assert state.owasp_violations and "A03" in state.owasp_violations[0]
    assert torn["called"] is True


async def test_low_coverage_escalates(make_agent, fake_llm, python_repo, monkeypatch) -> None:
    _patch_gates(monkeypatch, unit=_passed(62.0, passed=8))
    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.ESCALATE
    assert state.escalation_reason and "coverage" in state.escalation_reason.lower()


async def test_heal_cycles_exhausted_escalates(
    make_agent, fake_llm, python_repo, monkeypatch
) -> None:
    def unit_factory() -> TestSuiteResult:
        return TestSuiteResult(
            runner="pytest",
            status=GateStatus.FAILED,
            failed=1,
            coverage_pct=90.0,
            failures=[TestFailure(test_id="test_x", message="boom")],
        )

    _patch_gates(monkeypatch, unit_factory=unit_factory)
    fake_llm.heal_patches = [{"file_path": "app.py", "new_content": "x", "rationale": "fix"}]
    from app.agents.reviewer.tools import github

    async def fake_apply(sandbox: Any, files: dict, **kw: Any) -> list:
        return list(files.keys())

    monkeypatch.setattr(github, "apply_patches", fake_apply)

    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.ESCALATE
    assert state.heal_cycle == MAX_HEAL_CYCLES
    assert "cycles exhausted" in (state.escalation_reason or "").lower()


async def test_python_only_skips_typescript_gates(
    make_agent, fake_llm, python_repo, monkeypatch
) -> None:
    _patch_gates(monkeypatch, unit=_passed(90.0))

    async def eslint_must_not_run(sandbox: Any) -> list:
        raise AssertionError("ESLint must not run for a Python-only repo")

    async def playwright_must_not_run(sandbox: Any) -> TestSuiteResult:
        raise AssertionError("Playwright must not run for a Python-only repo")

    monkeypatch.setattr(eslint, "run", eslint_must_not_run)
    monkeypatch.setattr(playwright, "run", playwright_must_not_run)

    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.has_python is True
    assert state.has_typescript is False
    assert state.e2e_test_result is not None
    assert state.e2e_test_result.status is GateStatus.SKIPPED
    assert state.review_decision is ReviewDecision.APPROVED


async def test_sandbox_build_failure_escalates(
    make_agent, fake_llm, python_repo, monkeypatch
) -> None:
    from app.agents.reviewer.tools import sandbox as sandbox_tool

    async def boom(workdir: str, *, run_id: str, cycle: int = 0) -> Any:
        raise sandbox_tool.SandboxError("Docker build failed")

    monkeypatch.setattr(sandbox_tool, "spin_up", boom)
    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.ESCALATE
    assert state.fatal_error and "build failed" in state.fatal_error.lower()


async def test_sonarqube_down_still_reaches_verdict(
    make_agent, fake_llm, python_repo, monkeypatch
) -> None:
    _patch_gates(
        monkeypatch,
        unit=TestSuiteResult(runner="pytest", status=GateStatus.PASSED, coverage_pct=90.0),
        sonar=None,  # SonarQube unavailable
    )
    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.sonarqube_metrics is None
    assert state.review_decision is ReviewDecision.APPROVED


async def test_missing_repo_raises_understand_error(make_agent, fake_llm) -> None:
    agent = make_agent()
    with pytest.raises(AgentError):
        await agent.run(ReviewerInput(organization_id="o", repo_url=""))


async def test_dependency_cve_critical_escalates(
    make_agent, fake_llm, python_repo, monkeypatch
) -> None:
    # A non-fixable CRITICAL dependency CVE (OWASP A06) must hard-block, not approve.
    cve = SecurityFinding(
        tool="trivy",
        severity=SeverityLevel.CRITICAL,
        rule_id="CVE-2024-9",
        file_path="package-lock.json",
        message="Remote code execution",
        owasp_category=OWASPCategory.A06_VULNERABLE_COMPONENTS,
        auto_fixable=False,
    )
    _patch_gates(monkeypatch, unit=_passed(95.0), security=[cve])
    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.ESCALATE
    assert state.owasp_violations


async def test_crashed_unit_gate_escalates(make_agent, fake_llm, python_repo, monkeypatch) -> None:
    _patch_gates(monkeypatch, unit=_passed(90.0))

    async def crash(sandbox: Any) -> TestSuiteResult:
        raise RuntimeError("pytest crashed")

    monkeypatch.setattr(pytest_runner, "run", crash)

    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("app.agents.reviewer.utils.retry.asyncio.sleep", no_sleep)

    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.ESCALATE
    assert state.unit_test_result is None


async def test_heal_rejects_test_file_patch(make_agent, fake_llm, python_repo, monkeypatch) -> None:
    calls = {"n": 0}

    def unit_factory() -> TestSuiteResult:
        calls["n"] += 1
        if calls["n"] == 1:
            return TestSuiteResult(
                runner="pytest",
                status=GateStatus.FAILED,
                failed=1,
                coverage_pct=90.0,
                failures=[TestFailure(test_id="t", message="x")],
            )
        return _passed(90.0, passed=5)

    _patch_gates(monkeypatch, unit_factory=unit_factory)
    fake_llm.heal_patches = [
        {"file_path": "tests/test_app.py", "new_content": "assert True", "rationale": "cheat"},
        {"file_path": "app.py", "new_content": "x = 1", "rationale": "fix"},
    ]
    captured: dict[str, str] = {}
    from app.agents.reviewer.tools import github

    async def fake_apply(sandbox: Any, files: dict, **kw: Any) -> list:
        captured.update(files)
        return list(files.keys())

    monkeypatch.setattr(github, "apply_patches", fake_apply)

    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert "app.py" in captured
    assert "tests/test_app.py" not in captured  # D5: test-file patch rejected
    assert state.review_decision is ReviewDecision.APPROVED


async def test_heal_generation_failure_records_failed_outcome(
    make_agent, fake_llm, python_repo, monkeypatch
) -> None:
    def unit_factory() -> TestSuiteResult:
        return TestSuiteResult(
            runner="pytest",
            status=GateStatus.FAILED,
            failed=1,
            coverage_pct=90.0,
            failures=[TestFailure(test_id="t", message="x")],
        )

    _patch_gates(monkeypatch, unit_factory=unit_factory)
    fake_llm.fail_task_class = "reviewer_heal"  # heal LLM always throws
    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.ESCALATE
    assert state.heal_history
    assert state.heal_history[0].outcome == "failed"


async def test_triage_enrichment_failure_is_non_fatal(
    make_agent, fake_llm, python_repo, monkeypatch
) -> None:
    # A throwing triage LLM must not abort the run — the decision is deterministic.
    _patch_gates(monkeypatch, unit=_passed(62.0, passed=8))
    fake_llm.fail_task_class = "reviewer_triage"
    agent = make_agent()
    state = await agent.run(_input(python_repo))
    assert state.review_decision is ReviewDecision.ESCALATE
    assert "coverage" in (state.escalation_reason or "").lower()
