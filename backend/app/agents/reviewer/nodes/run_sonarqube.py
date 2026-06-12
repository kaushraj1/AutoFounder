"""Node 7 — run_sonarqube: quality gate (plan §3.4).

Returns ``None`` metrics when SonarQube is unconfigured/unreachable; the verdict
is still reached (fallback matrix: skip gate, quality_gate_passed=false).
"""

from __future__ import annotations

from typing import Any

from app.agents.reviewer.nodes._common import to_sandbox
from app.agents.reviewer.schema import ReviewerState
from app.agents.reviewer.tools import sonarqube
from app.agents.reviewer.utils.retry import with_retry
from app.core.config import get_settings


@with_retry("run_sonarqube")
async def run_sonarqube(state: ReviewerState, agent: Any) -> dict[str, Any]:
    settings = get_settings()
    sandbox = to_sandbox(state)
    metrics = await sonarqube.run(
        sandbox,
        base_url=settings.sonarqube_url or None,
        token=settings.sonarqube_token or None,
        project_key=settings.sonarqube_project_key or None,
    )
    return {"sonarqube_metrics": metrics}
