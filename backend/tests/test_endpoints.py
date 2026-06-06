"""Integration tests for REST API endpoints (ideas, runs, gates, artifacts, feedback, cost)."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.deps import get_udal
from app.main import create_app
from app.models.artifact import Artifact
from app.models.gate import Gate
from app.models.run import Run


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_udal(mock_db_session: AsyncMock) -> MagicMock:
    """Mock tenant-scoped UDAL."""
    udal = MagicMock()
    udal.organization_id = "org_test"

    # Mock relational context manager
    db_ctx = MagicMock()
    db_ctx.session = mock_db_session
    db_ctx.audit = AsyncMock()

    async def mock_enter(*args, **kwargs):
        return db_ctx

    async def mock_exit(*args, **kwargs):
        pass

    db_ctx_mgr = MagicMock()
    db_ctx_mgr.__aenter__ = mock_enter
    db_ctx_mgr.__aexit__ = mock_exit

    udal.relational.return_value = db_ctx_mgr
    return udal


@pytest.fixture
def test_client(mock_udal: MagicMock) -> Iterator[TestClient]:
    """FastAPI TestClient with UDAL dependency overridden."""
    app = create_app()
    app.dependency_overrides[get_udal] = lambda: mock_udal
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Ideas Endpoint Tests
# ---------------------------------------------------------------------------


def test_submit_idea_success(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    response = test_client.post(
        "/v1/ideas", json={"text": "A platform for auto-generating SaaS compliance."}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert data["data"]["pillar"] == "strategy"
    assert data["data"]["status"] == "pending"

    # Verify DB calls
    assert mock_db_session.add.call_count == 1
    assert mock_db_session.commit.call_count == 1


def test_submit_idea_invalid_short(test_client: TestClient) -> None:
    response = test_client.post("/v1/ideas", json={"text": "short"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["error"]["code"] == "AF_ERR_VALIDATION"


# ---------------------------------------------------------------------------
# Runs Endpoint Tests
# ---------------------------------------------------------------------------


def test_list_runs_paginated(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    # Mock count result
    count_result = MagicMock()
    count_result.scalar_one.return_value = 10

    # Mock list runs result
    run_1 = Run(id=uuid.uuid4(), pillar="strategy", status="pending")
    run_1.created_at = datetime.now(UTC)
    runs_result = MagicMock()
    runs_result.scalars.return_value.all.return_value = [run_1]

    mock_db_session.execute.side_effect = [count_result, runs_result]

    response = test_client.get("/v1/runs?limit=1&order=desc")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert data["pagination"]["total"] == 10
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == str(run_1.id)


def test_get_run_by_id_success(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    run_id = uuid.uuid4()
    run = Run(id=run_id, pillar="strategy", status="pending")
    run.created_at = datetime.now(UTC)

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = run
    mock_db_session.execute.return_value = db_result

    response = test_client.get(f"/v1/runs/{run_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["id"] == str(run_id)


def test_get_run_by_id_not_found(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = db_result

    response = test_client.get(f"/v1/runs/{uuid.uuid4()}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "AF_ERR_NOT_FOUND"


def test_cancel_run_success(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    run_id = uuid.uuid4()
    run = Run(id=run_id, pillar="strategy", status="pending")
    run.created_at = datetime.now(UTC)

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = run
    mock_db_session.execute.return_value = db_result

    response = test_client.delete(f"/v1/runs/{run_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] is True
    assert mock_db_session.delete.call_count == 1
    assert mock_db_session.commit.call_count == 1


# ---------------------------------------------------------------------------
# Gates Endpoint Tests
# ---------------------------------------------------------------------------


def test_decide_gate_approve_success(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    run_id = uuid.uuid4()
    gate_id = uuid.uuid4()

    run = Run(id=run_id, pillar="strategy", status="awaiting_gate")
    gate = Gate(id=gate_id, run_id=run_id, kind="validation_approve", state="pending", payload={})
    gate.created_at = datetime.now(UTC)

    gate_result = MagicMock()
    gate_result.scalar_one_or_none.return_value = gate
    run_result = MagicMock()
    run_result.scalar_one_or_none.return_value = run

    mock_db_session.execute.side_effect = [gate_result, run_result]

    with patch("app.orchestrator.engine.OrchestratorEngine") as mock_engine_cls:
        mock_engine = AsyncMock()
        mock_engine_cls.return_value = mock_engine

        response = test_client.post(
            f"/v1/runs/{run_id}/gates/{gate_id}",
            json={"decision": "approved", "notes": "Looks solid!"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["state"] == "approved"
        assert run.status == "running"
        assert mock_db_session.commit.call_count == 1
        mock_engine.resume.assert_awaited_once_with(
            run_id=str(run_id),
            gate_decision="approved",
            pivot_text="Looks solid!",
        )


def test_decide_gate_already_decided(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    run_id = uuid.uuid4()
    gate_id = uuid.uuid4()

    gate = Gate(id=gate_id, run_id=run_id, kind="validation_approve", state="approved", payload={})
    gate_result = MagicMock()
    gate_result.scalar_one_or_none.return_value = gate
    mock_db_session.execute.return_value = gate_result

    response = test_client.post(f"/v1/runs/{run_id}/gates/{gate_id}", json={"decision": "approved"})
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error"]["code"] == "AF_ERR_CONFLICT"


# ---------------------------------------------------------------------------
# Artifacts Endpoint Tests
# ---------------------------------------------------------------------------


def test_list_artifacts_success(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    run_id = uuid.uuid4()
    run = Run(id=run_id, pillar="strategy", status="pending")

    artifact = Artifact(
        id=uuid.uuid4(), run_id=run_id, kind="lean_canvas", uri="org_test/canvas.json"
    )
    artifact.created_at = datetime.now(UTC)

    run_result = MagicMock()
    run_result.scalar_one_or_none.return_value = run
    artifacts_result = MagicMock()
    artifacts_result.scalars.return_value.all.return_value = [artifact]

    mock_db_session.execute.side_effect = [run_result, artifacts_result]

    response = test_client.get(f"/v1/runs/{run_id}/artifacts")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["kind"] == "lean_canvas"


# ---------------------------------------------------------------------------
# Feedback Endpoint Tests
# ---------------------------------------------------------------------------


def test_submit_feedback_success(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    run_id = uuid.uuid4()
    run = Run(id=run_id, pillar="strategy", status="pending")

    run_result = MagicMock()
    run_result.scalar_one_or_none.return_value = run
    mock_db_session.execute.return_value = run_result

    response = test_client.post(
        "/v1/feedback", json={"run_id": str(run_id), "rating": 5, "comment": "Amazing!"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] is True


# ---------------------------------------------------------------------------
# LLMOps Endpoint Tests
# ---------------------------------------------------------------------------


def test_get_cost_success(test_client: TestClient, mock_db_session: AsyncMock) -> None:
    cost_result = MagicMock()
    cost_result.scalar.return_value = 15.75
    mock_db_session.execute.return_value = cost_result

    response = test_client.get("/v1/llmops/cost")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["total_cost_usd"] == 15.75
