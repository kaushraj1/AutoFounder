"""DevOpsAgent: wires the LangGraph subgraph."""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base import BaseAgent, VerifyError
from app.agents.devops.graph import build_devops_graph
from app.agents.devops.schema import DeployStatus, DevOpsState

logger = logging.getLogger("app.agents.devops")


class DevOpsAgent(BaseAgent[Any, DevOpsState]):
	PILLAR = 5
	AGENT_ID = "devops"
	SLA_SECONDS = 600

	def __init__(self, *args: object, **kwargs: object) -> None:
		super().__init__(*args, **kwargs)
		self.graph = build_devops_graph(self.checkpointer)

	async def understand(self, input_data: Any) -> dict[str, Any]:
		if isinstance(input_data, DevOpsState):
			return input_data.model_dump()
		if isinstance(input_data, dict):
			return input_data
		raise ValueError("DevOpsAgent input must be DevOpsState or dict")

	async def plan(self, intent: dict[str, Any]) -> dict[str, Any]:
		initial_state = DevOpsState.model_validate(intent)
		return {"initial_state": initial_state}

	async def execute(self, plan: dict[str, Any]) -> DevOpsState:
		initial_state: DevOpsState = plan["initial_state"]
		config = {"configurable": {"thread_id": str(initial_state.run_id)}}
		result = await self.graph.ainvoke(initial_state.model_dump(), config=config)
		return DevOpsState.model_validate(result)

	async def verify(self, output: DevOpsState) -> dict[str, Any]:
		issues: list[str] = []
		if output.deploy_status != DeployStatus.HEALTHY:
			issues.append(f"deploy_status={output.deploy_status}")
		if not output.live_url:
			issues.append("live_url missing")
		if not output.smoke_tests_passed:
			issues.append("smoke tests did not pass")

		if issues:
			raise VerifyError(
				"; ".join(issues),
				agent_id=self.AGENT_ID,
				run_id=str(output.run_id),
			)
		return {"passed": True, "issues": []}

	async def learn(self, trace: dict[str, Any]) -> None:
		logger.info(
			"DevOps run=%s status=%s smoke=%s",
			trace.get("run_id"),
			trace.get("deploy_status"),
			trace.get("smoke_tests_passed"),
		)