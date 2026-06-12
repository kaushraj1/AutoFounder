"""SonarQube quality-gate client → SonarMetrics | None (plan §3.4 node 7).

Returns ``None`` when SonarQube is not configured or unreachable — the node then
records ``quality_gate_passed = false`` and continues (fallback matrix: skip gate).
"""

from __future__ import annotations

import logging

import httpx

from app.agents.reviewer.schema import SonarMetrics
from app.agents.reviewer.tools.sandbox import Sandbox

logger = logging.getLogger("app.agents.reviewer.tools.sonarqube")

_METRIC_KEYS = "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density"


async def run(
    sandbox: Sandbox,
    *,
    base_url: str | None = None,
    token: str | None = None,
    project_key: str | None = None,
) -> SonarMetrics | None:
    """Fetch the quality-gate status + key measures. None if unavailable."""
    if not base_url or not token or not project_key:
        logger.warning("SonarQube not configured — skipping quality gate")
        return None

    base = base_url.rstrip("/")
    auth = (token, "")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            gate = await client.get(
                f"{base}/api/qualitygates/project_status",
                params={"projectKey": project_key},
                auth=auth,
            )
            gate.raise_for_status()
            passed = gate.json().get("projectStatus", {}).get("status") == "OK"

            measures = await client.get(
                f"{base}/api/measures/component",
                params={"component": project_key, "metricKeys": _METRIC_KEYS},
                auth=auth,
            )
            measures.raise_for_status()
            raw = {
                m["metric"]: m.get("value")
                for m in measures.json().get("component", {}).get("measures", [])
            }
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("SonarQube unavailable (%s) — skipping quality gate", exc)
        return None

    return SonarMetrics(
        quality_gate_passed=passed,
        bugs=_to_int(raw.get("bugs")),
        vulnerabilities=_to_int(raw.get("vulnerabilities")),
        code_smells=_to_int(raw.get("code_smells")),
        coverage_pct=_to_float(raw.get("coverage")),
        duplicated_lines_pct=_to_float(raw.get("duplicated_lines_density")),
    )


def _to_int(v: str | None) -> int:
    try:
        return int(float(v)) if v is not None else 0
    except (TypeError, ValueError):
        return 0


def _to_float(v: str | None) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
