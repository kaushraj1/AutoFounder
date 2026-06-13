"""Conditional-edge routers for the DevOps subgraph."""

from __future__ import annotations

from app.agents.devops.schema import ApprovalStatus, DeployStatus, DevOpsState


def route_after_hitl(state: DevOpsState) -> str:
    if state.approval_status == ApprovalStatus.APPROVED:
        return "attach_foundation_network"
    return "error_handler"


def route_after_deploy(state: DevOpsState) -> str:
    if state.deploy_status == DeployStatus.HEALTHY:
        return "configure_dns_ssl"
    return "error_handler"


def route_after_smoke(state: DevOpsState) -> str:
    if state.smoke_tests_passed:
        return "render_deploy_report"
    return "error_handler"
