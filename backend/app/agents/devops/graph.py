"""LangGraph StateGraph factory for the DevOps agent."""

from __future__ import annotations

from functools import partial
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.devops import nodes
from app.agents.devops.routers import route_after_deploy, route_after_hitl, route_after_smoke
from app.agents.devops.schema import DevOpsState


async def _infra_join(_: dict) -> dict:
	return {}


async def _deploy_join(_: dict) -> dict:
	return {}


async def _postdeploy_join(_: dict) -> dict:
	return {}


def build_devops_graph(
	agent: Any | None = None, checkpointer: object | None = None
) -> object:
	"""Build the DevOps StateGraph.

	``agent`` is required for the four LLM-driven nodes
	(build_task_defs, configure_cicd, configure_monitoring,
	render_deploy_report). If None is passed, those nodes will raise at
	runtime — keep this signature optional only for the run_local CLI's
	non-execute dry inspect path.
	"""
	graph = StateGraph(DevOpsState)

	graph.add_node("ingest_input", nodes.ingest_input)
	graph.add_node("hitl_spend_gate", nodes.hitl_spend_gate)
	graph.add_node("attach_foundation_network", nodes.attach_foundation_network)
	graph.add_node("provision_compute", nodes.provision_compute)
	graph.add_node("provision_data_layer", nodes.provision_data_layer)
	graph.add_node("infra_join", _infra_join)
	graph.add_node("provision_secrets", nodes.provision_secrets)
	graph.add_node("build_task_defs", partial(nodes.build_task_defs, agent=agent))
	graph.add_node("configure_codedeploy", nodes.configure_codedeploy)
	graph.add_node("deploy_join", _deploy_join)
	graph.add_node("deploy_application", nodes.deploy_application)
	graph.add_node("configure_dns_ssl", nodes.configure_dns_ssl)
	graph.add_node(
		"configure_monitoring", partial(nodes.configure_monitoring, agent=agent)
	)
	graph.add_node("configure_cicd", partial(nodes.configure_cicd, agent=agent))
	graph.add_node("postdeploy_join", _postdeploy_join)
	graph.add_node("smoke_test", nodes.smoke_test)
	graph.add_node(
		"render_deploy_report", partial(nodes.render_deploy_report, agent=agent)
	)
	graph.add_node("error_handler", nodes.error_handler)

	graph.set_entry_point("ingest_input")
	graph.add_edge("ingest_input", "hitl_spend_gate")

	graph.add_conditional_edges(
		"hitl_spend_gate",
		route_after_hitl,
		{
			"attach_foundation_network": "attach_foundation_network",
			"error_handler": "error_handler",
		},
	)

	graph.add_edge("attach_foundation_network", "provision_compute")
	graph.add_edge("attach_foundation_network", "provision_data_layer")
	graph.add_edge("provision_compute", "infra_join")
	graph.add_edge("provision_data_layer", "infra_join")
	graph.add_edge("infra_join", "provision_secrets")

	graph.add_edge("provision_secrets", "build_task_defs")
	graph.add_edge("provision_secrets", "configure_codedeploy")
	graph.add_edge("build_task_defs", "deploy_join")
	graph.add_edge("configure_codedeploy", "deploy_join")
	graph.add_edge("deploy_join", "deploy_application")

	graph.add_conditional_edges(
		"deploy_application",
		route_after_deploy,
		{
			"configure_dns_ssl": "configure_dns_ssl",
			"error_handler": "error_handler",
		},
	)

	graph.add_edge("configure_dns_ssl", "configure_monitoring")
	graph.add_edge("configure_dns_ssl", "configure_cicd")
	graph.add_edge("configure_monitoring", "postdeploy_join")
	graph.add_edge("configure_cicd", "postdeploy_join")
	graph.add_edge("postdeploy_join", "smoke_test")

	graph.add_conditional_edges(
		"smoke_test",
		route_after_smoke,
		{
			"render_deploy_report": "render_deploy_report",
			"error_handler": "error_handler",
		},
	)

	graph.add_edge("render_deploy_report", END)
	graph.add_edge("error_handler", END)

	if checkpointer is None:
		return graph.compile()
	return graph.compile(checkpointer=checkpointer)