"""Reviewer tool registry (AF-047 catalog + BaseAgent DI slot).

The Reviewer's tools are strongly-typed functions invoked directly by nodes
(``tools/*.py``), so dynamic ``call()`` dispatch is intentionally unsupported —
this registry exists to (a) satisfy ``BaseAgent``'s ``tool_registry`` dependency
and (b) declare the tool catalog the platform Tool Registry (AF-047) registers.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import ToolRegistryProtocol

# AF-047 tool catalog: name → scope/auth/cost/rate-limit metadata (plan §10.4).
REVIEWER_TOOLS: dict[str, dict[str, str]] = {
    "spin_sandbox": {"scope": "reviewer", "auth": "docker", "cost": "compute"},
    "teardown_sandbox": {"scope": "reviewer", "auth": "docker", "cost": "compute"},
    "eslint": {"scope": "reviewer", "auth": "none", "cost": "free"},
    "python_lint": {"scope": "reviewer", "auth": "none", "cost": "free"},
    "jest": {"scope": "reviewer", "auth": "none", "cost": "free"},
    "pytest": {"scope": "reviewer", "auth": "none", "cost": "free"},
    "playwright": {"scope": "reviewer", "auth": "none", "cost": "free"},
    "trivy_scanner": {"scope": "reviewer+devops", "auth": "none", "cost": "free"},
    "semgrep_scanner": {"scope": "reviewer", "auth": "api_key", "cost": "low"},
    "bandit_scanner": {"scope": "reviewer", "auth": "none", "cost": "free"},
    "snyk_scanner": {"scope": "reviewer", "auth": "api_key", "cost": "medium"},
    "gitleaks_scanner": {"scope": "reviewer", "auth": "none", "cost": "free"},
    "sonarqube": {"scope": "reviewer", "auth": "token", "cost": "free"},
    "github_pr_comment": {"scope": "reviewer+engineering", "auth": "oauth", "cost": "free"},
    "github_commit": {"scope": "reviewer+engineering", "auth": "oauth", "cost": "free"},
}


class ReviewerToolRegistry(ToolRegistryProtocol):
    """Catalog registry for the Reviewer agent (typed tools are called directly)."""

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            f"Reviewer tools are typed and invoked directly by nodes, not via "
            f"dynamic call() (attempted: '{tool_name}'). See app/agents/reviewer/tools/."
        )

    @staticmethod
    def registered_tools() -> dict[str, dict[str, str]]:
        """Return the AF-047 tool catalog for platform registration."""
        return dict(REVIEWER_TOOLS)
