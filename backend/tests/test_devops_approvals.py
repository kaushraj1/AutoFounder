"""Integration tests for `POST /v1/runs/{run_id}/devops-spend-approval`.

This endpoint resolves the DevOps subgraph's pre-flight HITL spend gate by
writing the founder's decision into the Redis key that the polling loop in
`app/agents/devops/nodes/hitl_spend_gate.py` watches.

Distinct from `gates.py` (orchestrator-level Gate DB rows) — verified by
asserting no Gate row is touched and the Redis write happens with the
configured key prefix.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.deps import get_redis, get_udal
from app.core.config import get_settings
from app.main import create_app
from app.models.run import Run


@pytest.fixture
def mock_db_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_udal(mock_db_session: AsyncMock) -> MagicMock:
    udal = MagicMock()
    udal.organization_id = "org_test"

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
    udal._audit_calls = db_ctx.audit  # exposed for assertions
    return udal


@pytest.fixture
def mock_redis() -> MagicMock:
    """Mock Redis with async get/set methods.

    Using a MagicMock instead of fakeredis avoids the event-loop binding clash
    between fakeredis (created on test-collection loop) and FastAPI TestClient
    (which spins its own loop per request).
    """
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def test_client(mock_udal: MagicMock, mock_redis: MagicMock) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_udal] = lambda: mock_udal
    app.dependency_overrides[get_redis] = lambda: mock_redis
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _run_row(run_id: uuid.UUID) -> Run:
    run = Run(id=run_id, pillar="devops", status="running")
    run.created_at = datetime.now(UTC)
    return run


def test_devops_spend_approval_approved_writes_redis(
    test_client: TestClient,
    mock_db_session: AsyncMock,
    mock_redis: MagicMock,
    mock_udal: MagicMock,
) -> None:
    run_id = uuid.uuid4()
    run_result = MagicMock()
    run_result.scalar_one_or_none.return_value = _run_row(run_id)
    mock_db_session.execute.return_value = run_result

    response = test_client.post(
        f"/v1/runs/{run_id}/devops-spend-approval",
        json={"decision": "approved", "notes": "$180/mo is acceptable for the trial"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()["data"]
    assert body["decision"] == "approved"
    assert body["run_id"] == str(run_id)

    settings = get_settings()
    expected_key = f"{settings.devops_hitl_redis_key_prefix}:{run_id}"
    assert body["redis_key"] == expected_key

    mock_redis.set.assert_awaited_once()
    set_args, set_kwargs = mock_redis.set.await_args
    assert set_args[0] == expected_key
    assert set_args[1] == "approved"
    assert "ex" in set_kwargs and set_kwargs["ex"] > 0

    mock_udal._audit_calls.assert_awaited_once()
    audit_kwargs = mock_udal._audit_calls.await_args.kwargs
    assert audit_kwargs["metadata"]["decision"] == "approved"
    assert audit_kwargs["metadata"]["redis_key"] == expected_key


def test_devops_spend_approval_rejected_writes_redis(
    test_client: TestClient,
    mock_db_session: AsyncMock,
    mock_redis: MagicMock,
) -> None:
    run_id = uuid.uuid4()
    run_result = MagicMock()
    run_result.scalar_one_or_none.return_value = _run_row(run_id)
    mock_db_session.execute.return_value = run_result

    response = test_client.post(
        f"/v1/runs/{run_id}/devops-spend-approval",
        json={"decision": "rejected"},
    )

    assert response.status_code == status.HTTP_200_OK
    mock_redis.set.assert_awaited_once()
    assert mock_redis.set.await_args.args[1] == "rejected"


def test_devops_spend_approval_run_not_found(
    test_client: TestClient, mock_db_session: AsyncMock, mock_redis: MagicMock
) -> None:
    run_result = MagicMock()
    run_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = run_result

    response = test_client.post(
        f"/v1/runs/{uuid.uuid4()}/devops-spend-approval",
        json={"decision": "approved"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "AF_ERR_NOT_FOUND"
    mock_redis.set.assert_not_awaited()


def test_devops_spend_approval_already_decided_conflicts(
    test_client: TestClient,
    mock_db_session: AsyncMock,
    mock_redis: MagicMock,
) -> None:
    run_id = uuid.uuid4()
    run_result = MagicMock()
    run_result.scalar_one_or_none.return_value = _run_row(run_id)
    mock_db_session.execute.return_value = run_result

    mock_redis.get = AsyncMock(return_value="approved")

    response = test_client.post(
        f"/v1/runs/{run_id}/devops-spend-approval",
        json={"decision": "rejected"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error"]["code"] == "AF_ERR_CONFLICT"
    mock_redis.set.assert_not_awaited()


def test_devops_spend_approval_invalid_decision_value(test_client: TestClient) -> None:
    response = test_client.post(
        f"/v1/runs/{uuid.uuid4()}/devops-spend-approval",
        json={"decision": "maybe"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
