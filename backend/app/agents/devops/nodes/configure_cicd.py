"""Commit GitHub Actions workflow to the tenant repo."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import CICDConfig, NodeStatus, NodeTrace


async def configure_cicd(state: dict) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	workflow = """name: deploy\non:\n  push:\n    branches: [main]\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n"""
	cd_app = state.get("codedeploy_app")
	codedeploy_app = None
	if isinstance(cd_app, dict):
		codedeploy_app = cd_app.get("app_name")
	elif cd_app is not None:
		codedeploy_app = getattr(cd_app, "app_name", None)
	return {
		"cicd_config": CICDConfig(
			workflow_file_path=".github/workflows/deploy.yml",
			workflow_yaml=workflow,
			codedeploy_app_name=codedeploy_app,
			ecr_registry=state.get("ecr_registry"),
		),
		"node_traces": [
			NodeTrace(
				node="configure_cicd",
				status=NodeStatus.COMPLETED,
				started_at=now,
				completed_at=now,
			)
		],
	}