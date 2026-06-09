"""Unit — tool wrappers: parse real CLI output + graceful skip when binary absent.

Everything is driven by monkeypatching the single subprocess/exec seam, so no
real Docker / scanners / node / pytest binaries are required.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from app.agents.reviewer.schema import GateStatus, OWASPCategory, SeverityLevel
from app.agents.reviewer.tools import (
    bandit,
    eslint,
    github,
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
from app.agents.reviewer.tools._subprocess import CommandResult
from app.agents.reviewer.tools.sandbox import Sandbox

SANDBOX = Sandbox(workdir="/tmp/repo")


def _cmd(stdout: str = "", returncode: int = 0, stderr: str = "") -> CommandResult:
    return CommandResult(returncode=returncode, stdout=stdout, stderr=stderr)


# ---------------------------------------------------------------------------
# Security scanners (run_command seam)
# ---------------------------------------------------------------------------


async def test_trivy_parses_vulnerabilities(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "Results": [
            {
                "Target": "package-lock.json",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2024-1",
                        "PkgName": "lodash",
                        "Severity": "HIGH",
                        "Title": "Prototype pollution",
                        "FixedVersion": "4.17.21",
                        "CweIDs": ["CWE-1321"],
                    }
                ],
            }
        ]
    }
    monkeypatch.setattr(trivy, "binary_available", lambda b: True)

    async def fake_run(*a: Any, **kw: Any) -> CommandResult:
        return _cmd(json.dumps(payload))

    monkeypatch.setattr(trivy, "run_command", fake_run)
    findings = await trivy.run(SANDBOX)
    assert len(findings) == 1
    assert findings[0].tool == "trivy"
    assert findings[0].severity is SeverityLevel.HIGH
    assert findings[0].owasp_category is OWASPCategory.A06_VULNERABLE_COMPONENTS
    assert findings[0].auto_fixable is True


async def test_trivy_skips_when_binary_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(trivy, "binary_available", lambda b: False)
    assert await trivy.run(SANDBOX) == []


async def test_gitleaks_marks_critical_hard_block(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [{"RuleID": "aws-key", "File": ".env", "StartLine": 3, "Description": "AWS key"}]
    monkeypatch.setattr(gitleaks, "binary_available", lambda b: True)

    async def fake_run(args: list[str], **kw: Any) -> CommandResult:
        report_path = args[args.index("--report-path") + 1]
        Path(report_path).write_text(json.dumps(payload), encoding="utf-8")
        return _cmd("", returncode=1)  # gitleaks rc=1 → leaks found

    monkeypatch.setattr(gitleaks, "run_command", fake_run)
    findings = await gitleaks.run(SANDBOX)
    assert findings[0].severity is SeverityLevel.CRITICAL
    assert findings[0].owasp_category is OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES
    assert findings[0].auto_fixable is False


async def test_bandit_maps_sql_injection(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "results": [
            {
                "test_id": "B608",
                "filename": "app/db.py",
                "line_number": 12,
                "issue_severity": "HIGH",
                "issue_text": "Possible SQL injection",
                "issue_cwe": {"id": 89},
            }
        ]
    }
    monkeypatch.setattr(bandit, "binary_available", lambda b: True)

    async def fake_run(*a: Any, **kw: Any) -> CommandResult:
        return _cmd(json.dumps(payload))

    monkeypatch.setattr(bandit, "run_command", fake_run)
    findings = await bandit.run(SANDBOX)
    assert findings[0].owasp_category is OWASPCategory.A03_INJECTION
    assert findings[0].cwe == "CWE-89"


async def test_semgrep_maps_owasp_from_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "results": [
            {
                "check_id": "python.lang.security.injection",
                "path": "app/views.py",
                "start": {"line": 22},
                "extra": {
                    "severity": "ERROR",
                    "message": "Injection risk",
                    "metadata": {"owasp": ["A03:2021 - Injection"], "cwe": ["CWE-89"]},
                },
            }
        ]
    }
    monkeypatch.setattr(semgrep, "binary_available", lambda b: True)

    async def fake_run(*a: Any, **kw: Any) -> CommandResult:
        return _cmd(json.dumps(payload))

    monkeypatch.setattr(semgrep, "run_command", fake_run)
    findings = await semgrep.run(SANDBOX)
    assert findings[0].severity is SeverityLevel.HIGH
    assert findings[0].owasp_category is OWASPCategory.A03_INJECTION


async def test_snyk_skips_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(snyk, "binary_available", lambda b: True)
    assert await snyk.run(SANDBOX, token=None) == []


# ---------------------------------------------------------------------------
# Lint / test runners (exec_in seam)
# ---------------------------------------------------------------------------


async def test_pytest_parses_summary_and_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout = (
        "FAILED tests/test_x.py::test_add - assert 3 == 4\n"
        "3 passed, 1 failed in 0.5s\n"
        "TOTAL      120     30    75%\n"
    )
    monkeypatch.setattr(pytest_runner, "binary_available", lambda b: True)

    async def fake_exec(sandbox: Any, args: list[str], **kw: Any) -> CommandResult:
        return _cmd(stdout, returncode=1)

    monkeypatch.setattr(pytest_runner, "exec_in", fake_exec)
    result = await pytest_runner.run(SANDBOX)
    assert result.status is GateStatus.FAILED
    assert result.passed == 3
    assert result.failed == 1
    assert result.coverage_pct == 75.0
    assert result.failures and result.failures[0].test_id == "tests/test_x.py::test_add"


async def test_pytest_skips_when_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pytest_runner, "binary_available", lambda b: False)
    result = await pytest_runner.run(SANDBOX)
    assert result.status is GateStatus.SKIPPED


async def test_eslint_parses_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    eslint_json = json.dumps(
        [
            {
                "filePath": "src/a.ts",
                "errorCount": 2,
                "warningCount": 1,
                "fixableErrorCount": 2,
                "fixableWarningCount": 0,
                "messages": [{"line": 1, "ruleId": "no-unused", "message": "unused"}],
            }
        ]
    )
    monkeypatch.setattr(eslint, "binary_available", lambda b: True)

    async def fake_exec(sandbox: Any, args: list[str], **kw: Any) -> CommandResult:
        if "eslint" in args:
            return _cmd(eslint_json, returncode=1)
        return _cmd("", returncode=0)  # prettier --check passes

    monkeypatch.setattr(eslint, "exec_in", fake_exec)
    results = await eslint.run(SANDBOX)
    by_tool = {r.tool: r for r in results}
    assert by_tool["eslint"].status is GateStatus.FAILED
    assert by_tool["eslint"].error_count == 2
    assert by_tool["eslint"].fixable_count == 2
    assert by_tool["prettier"].status is GateStatus.PASSED


async def test_jest_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    jest_json = {
        "success": False,
        "numTotalTests": 5,
        "numPassedTests": 4,
        "numFailedTests": 1,
        "numPendingTests": 0,
        "testResults": [
            {
                "name": "Button.test.tsx",
                "assertionResults": [
                    {"status": "failed", "fullName": "renders", "failureMessages": ["boom"]}
                ],
            }
        ],
    }
    stdout = f"Statements : 88% ( 44/50 )\n{json.dumps(jest_json)}\n"
    monkeypatch.setattr(jest, "binary_available", lambda b: True)

    async def fake_exec(sandbox: Any, args: list[str], **kw: Any) -> CommandResult:
        return _cmd(stdout, returncode=1)

    monkeypatch.setattr(jest, "exec_in", fake_exec)
    result = await jest.run(SANDBOX)
    assert result.status is GateStatus.FAILED
    assert result.passed == 4
    assert result.failed == 1
    assert result.coverage_pct == 88.0


async def test_python_lint_parses_ruff_and_black(monkeypatch: pytest.MonkeyPatch) -> None:
    ruff_json = json.dumps(
        [
            {
                "code": "F401",
                "message": "unused import",
                "filename": "a.py",
                "location": {"row": 1},
                "fix": {"applicability": "safe"},
            }
        ]
    )
    monkeypatch.setattr(python_lint, "binary_available", lambda b: True)

    async def fake_exec(sandbox: Any, args: list[str], **kw: Any) -> CommandResult:
        if "ruff" in args:
            return _cmd(ruff_json, returncode=1)
        return _cmd("", returncode=0)  # black --check passes

    monkeypatch.setattr(python_lint, "exec_in", fake_exec)
    results = await python_lint.run(SANDBOX)
    by_tool = {r.tool: r for r in results}
    assert by_tool["ruff"].status is GateStatus.FAILED
    assert by_tool["ruff"].error_count == 1
    assert by_tool["ruff"].fixable_count == 1
    assert by_tool["black"].status is GateStatus.PASSED


async def test_playwright_parses_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "stats": {"expected": 3, "unexpected": 1, "flaky": 0, "skipped": 0},
        "suites": [
            {"file": "e2e.spec.ts", "specs": [{"title": "login", "ok": False}], "suites": []}
        ],
    }
    monkeypatch.setattr(playwright, "binary_available", lambda b: True)

    async def fake_exec(sandbox: Any, args: list[str], **kw: Any) -> CommandResult:
        return _cmd(json.dumps(payload), returncode=1)

    monkeypatch.setattr(playwright, "exec_in", fake_exec)
    result = await playwright.run(SANDBOX)
    assert result.status is GateStatus.FAILED
    assert result.passed == 3
    assert result.failed == 1
    assert result.failures


async def test_snyk_parses_vulnerabilities(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "displayTargetFile": "package.json",
        "vulnerabilities": [
            {
                "id": "SNYK-JS-1",
                "severity": "high",
                "packageName": "lodash",
                "title": "Prototype pollution",
                "identifiers": {"CWE": ["CWE-1321"]},
                "fixedIn": ["4.17.21"],
            }
        ],
    }
    monkeypatch.setattr(snyk, "binary_available", lambda b: True)

    async def fake_run(*a: Any, **kw: Any) -> CommandResult:
        return _cmd(json.dumps(payload), returncode=1)

    monkeypatch.setattr(snyk, "run_command", fake_run)
    findings = await snyk.run(SANDBOX, token="tok")
    assert findings[0].tool == "snyk"
    assert findings[0].owasp_category is OWASPCategory.A06_VULNERABLE_COMPONENTS
    assert findings[0].auto_fixable is True


@respx.mock
async def test_sonarqube_maps_quality_gate() -> None:
    respx.get(url__regex=r".*/api/qualitygates/project_status.*").mock(
        return_value=httpx.Response(200, json={"projectStatus": {"status": "OK"}})
    )
    respx.get(url__regex=r".*/api/measures/component.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "component": {
                    "measures": [
                        {"metric": "bugs", "value": "2"},
                        {"metric": "coverage", "value": "81.5"},
                    ]
                }
            },
        )
    )
    metrics = await sonarqube.run(
        SANDBOX, base_url="https://sonar.example.com", token="t", project_key="proj"
    )
    assert metrics is not None
    assert metrics.quality_gate_passed is True
    assert metrics.bugs == 2
    assert metrics.coverage_pct == 81.5


@respx.mock
async def test_sonarqube_http_error_returns_none() -> None:
    respx.get(url__regex=r".*/api/qualitygates/project_status.*").mock(
        return_value=httpx.Response(503)
    )
    metrics = await sonarqube.run(
        SANDBOX, base_url="https://sonar.example.com", token="t", project_key="proj"
    )
    assert metrics is None


async def test_apply_patches_writes_source_and_refuses_escapes(tmp_path: Path) -> None:
    sandbox = Sandbox(workdir=str(tmp_path))
    written = await github.apply_patches(
        sandbox,
        {
            "src/a.py": "x = 1\n",
            "../evil.py": "bad",  # parent-dir escape
        },
    )
    assert written == ["src/a.py"]
    assert (tmp_path / "src" / "a.py").read_text(encoding="utf-8") == "x = 1\n"
    assert not (tmp_path.parent / "evil.py").exists()


async def test_apply_patches_refuses_sibling_prefix_escape(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    sandbox = Sandbox(workdir=str(repo))
    written = await github.apply_patches(sandbox, {"../repo-evil/payload.py": "bad"})
    assert written == []
    assert not (tmp_path / "repo-evil" / "payload.py").exists()


async def test_apply_patches_refuses_absolute_path(tmp_path: Path) -> None:
    sandbox = Sandbox(workdir=str(tmp_path))
    abs_target = str(tmp_path.parent / "abs.py")
    written = await github.apply_patches(sandbox, {abs_target: "bad"})
    assert written == []


async def test_post_pr_comment_without_token_returns_none() -> None:
    url = await github.post_pr_comment("https://github.com/o/r", 1, "body", token=None)
    assert url is None
