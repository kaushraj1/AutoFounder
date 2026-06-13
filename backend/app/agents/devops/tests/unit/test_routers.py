from uuid import uuid4

from app.agents.devops.routers import route_after_deploy, route_after_hitl, route_after_smoke
from app.agents.devops.schema import ApprovalStatus, DeployStatus, DevOpsState


def _state() -> DevOpsState:
    return DevOpsState.model_validate(
        {
            "run_id": str(uuid4()),
            "parent_run_id": str(uuid4()),
            "grandparent_run_id": str(uuid4()),
            "organization_id": "tenant-acme",
            "idea_normalised": "AI coach",
            "domain": "HealthTech",
            "repo_url": "https://github.com/org/repo",
            "services": [{"name": "api", "image_uri": "img", "port": 8000}],
        }
    )


def test_route_after_hitl_approved() -> None:
    state = _state()
    state.approval_status = ApprovalStatus.APPROVED
    assert route_after_hitl(state) == "attach_foundation_network"


def test_route_after_deploy_failed() -> None:
    state = _state()
    state.deploy_status = DeployStatus.FAILED
    assert route_after_deploy(state) == "error_handler"


def test_route_after_smoke_passed() -> None:
    state = _state()
    state.smoke_tests_passed = True
    assert route_after_smoke(state) == "render_deploy_report"
