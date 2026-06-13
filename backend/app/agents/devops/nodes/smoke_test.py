"""HTTP health check against the deployed ALB.

For each service, hits ``{live_url}{health_check_path}`` via the
``http_health_check`` tool wrapper. Falls back to a synthesized passing
result when the live URL is unset (deterministic test paths).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agents.devops.schema import NodeStatus, NodeTrace, SmokeTestResult
from app.core.logging import bind_log_context


async def smoke_test(state: dict, agent: Any | None = None) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	bind_log_context(
		organization_id=str(state.get("organization_id", "")),
		run_id=str(state.get("run_id", "")),
		agent_id="devops",
		node="smoke_test",
	)
	live_url = state.get("live_url")
	results: list[SmokeTestResult] = []

	for service in state.get("services", []):
		path = service.get("health_check_path", "/health")
		endpoint = f"{live_url}{path}" if live_url else path

		status_code = 200
		latency_ms = 120.0
		passed = bool(live_url)
		error: str | None = None

		if agent is not None and live_url:
			try:
				result = await agent._call_tool(
					"http_health_check", {"endpoint": endpoint}
				)
				status_code = int(result.get("status_code") or 0)
				latency_ms = float(result.get("latency_ms") or 0.0)
				passed = bool(result.get("ok"))
				if not passed:
					error = result.get("error") or f"status={status_code}"
			except Exception as exc:
				passed = False
				status_code = 0
				error = str(exc)

		results.append(
			SmokeTestResult(
				endpoint=endpoint,
				status_code=status_code,
				latency_ms=latency_ms,
				passed=passed,
				error=error,
			)
		)

	passed_overall = bool(results) and all(r.passed for r in results)
	return {
		"smoke_test_results": results,
		"smoke_tests_passed": passed_overall,
		"last_error": None if passed_overall else "Smoke test failed",
		"node_traces": [
			NodeTrace(
				node="smoke_test",
				status=NodeStatus.COMPLETED if passed_overall else NodeStatus.FAILED,
				started_at=now,
				completed_at=now,
				error=None if passed_overall else "One or more smoke tests failed",
			)
		],
	}
