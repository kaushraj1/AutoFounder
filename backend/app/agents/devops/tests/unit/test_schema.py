from uuid import UUID, uuid4

from app.agents.devops.schema import ApprovalStatus, DevOpsState


def _base_payload() -> dict:
    return {
        "run_id": str(uuid4()),
        "parent_run_id": str(uuid4()),
        "grandparent_run_id": str(uuid4()),
        "organization_id": "tenant-acme",
        "idea_normalised": "AI coach",
        "domain": "HealthTech",
        "repo_url": "https://github.com/org/repo",
        "services": [
            {
                "name": "api",
                "image_uri": "123.dkr.ecr.ap-south-1.amazonaws.com/api:latest",
                "port": 8000,
            }
        ],
    }


def test_devops_state_accepts_minimal_payload() -> None:
    state = DevOpsState.model_validate(_base_payload())
    assert isinstance(state.run_id, UUID)
    assert state.approval_status == ApprovalStatus.PENDING


def test_devops_state_ignores_extra_fields() -> None:
    payload = _base_payload()
    payload["unknown_field"] = "ignored"
    state = DevOpsState.model_validate(payload)
    assert state.organization_id == "tenant-acme"
