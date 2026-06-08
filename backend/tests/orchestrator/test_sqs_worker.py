"""Unit and integration tests for SQSPillarWorker (AF-035)."""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.events.producer import clear_event_log, get_event_log
from app.orchestrator.worker import SQSPillarWorker, get_mock_pillar_queue


# Ensure EventBridge log is clean for every test
@pytest.fixture(autouse=True)
def setup_teardown_event_log():
    clear_event_log()
    yield
    clear_event_log()


@pytest.fixture
def mock_session_factory():
    """Mock SQLAlchemy SessionLocal context manager yielding an AsyncMock session."""
    session = AsyncMock()
    mock_factory = MagicMock()

    class AsyncContextManagerMock:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_factory.return_value = AsyncContextManagerMock()
    return mock_factory, session


class MockEvent:
    """Mock gRPC Event matching StepEventProto layout."""

    def __init__(self, step_id: str, event_type: str, payload: bytes, timestamp: int):
        self.step_id = step_id
        self.event_type = event_type
        self.payload = payload
        self.timestamp = timestamp


@pytest.mark.asyncio
async def test_mock_queue_polling_and_run_resumption(mock_session_factory):
    """Verify worker polls mock queue, invokes gRPC, commits step events, and resumes the run."""
    mock_factory, session = mock_session_factory

    run_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    payload = {
        "run_id": run_id,
        "organization_id": org_id,
        "pillar": "1",
        "step_id": "strategy.understand",
        "agent_id": "strategist",
        "input": {"prompt": "test product"},
    }

    # Yield 3 events in gRPC stream
    async def mock_grpc_dispatcher(pl):
        yield MockEvent(pl["step_id"], "started", b'{"started": true}', 1600000000000)
        yield MockEvent(pl["step_id"], "progress", b'{"progress": 50}', 1600000001000)
        yield MockEvent(pl["step_id"], "completed", b'{"result": "success"}', 1600000002000)

    engine = AsyncMock()
    worker = SQSPillarWorker(
        engine=engine,
        redis=None,
        mock_grpc_dispatcher=mock_grpc_dispatcher,
    )

    # Push task to mock pillar queue
    queue = get_mock_pillar_queue("1")
    # Empty queue first to be clean
    while not queue.empty():
        queue.get_nowait()
    await queue.put(payload)

    # Patch SessionLocal to use our mock
    with patch("app.orchestrator.worker.SessionLocal", new=mock_factory):
        # Run one iteration of _poll_mock
        await worker._poll_mock("1")

    # Assert engine resume was called with "approved"
    engine.resume.assert_called_once_with(run_id=run_id, gate_decision="approved")

    # Assert SQL statements executed (SET LOCAL search_path + INSERTs)
    assert session.execute.call_count >= 4  # 1 for search_path, 3 for insert statements

    # Assert commit was called
    session.commit.assert_called_once()

    # Extract insert statements and verify values
    insert_calls = []
    for call in session.execute.call_args_list:
        stmt = call[0][0]
        params = call[1].get("params") or call[0][1] if len(call[0]) > 1 else {}
        sql = " ".join(str(stmt).split()).upper()
        if "INSERT INTO STEP_EVENTS" in sql:
            insert_calls.append(params)

    assert len(insert_calls) == 3
    assert insert_calls[0]["run_id"] == run_id
    assert insert_calls[0]["organization_id"] == org_id
    assert insert_calls[0]["pillar"] == "1"
    assert insert_calls[0]["agent_id"] == "strategist"
    assert insert_calls[0]["event_type"] == "started"
    assert json.loads(insert_calls[0]["payload"]) == {"started": True}
    assert insert_calls[0]["occurred_at"] == datetime.fromtimestamp(1600000000.0, tz=UTC)

    assert insert_calls[1]["event_type"] == "progress"
    assert json.loads(insert_calls[1]["payload"]) == {"progress": 50}

    assert insert_calls[2]["event_type"] == "completed"
    assert json.loads(insert_calls[2]["payload"]) == {"result": "success"}


@pytest.mark.asyncio
async def test_retry_backoff_and_jitter(mock_session_factory):
    """Verify transient error triggers sleep backoff with jitter and re-queues mock task."""
    mock_factory, session = mock_session_factory

    run_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    payload = {
        "run_id": run_id,
        "organization_id": org_id,
        "pillar": "2",
        "step_id": "architecture.generate",
        "agent_id": "architect",
        "retry_count": 1,  # Second attempt (1 retry so far)
    }

    # Simulate gRPC crash/timeout
    async def failing_grpc_dispatcher(pl):
        raise ConnectionResetError("Connection reset by worker")
        yield  # make it a generator

    engine = AsyncMock()
    worker = SQSPillarWorker(
        engine=engine,
        redis=None,
        mock_grpc_dispatcher=failing_grpc_dispatcher,
    )

    queue = get_mock_pillar_queue("2")
    while not queue.empty():
        queue.get_nowait()
    await queue.put(payload)

    original_sleep = asyncio.sleep
    sleep_calls = []

    async def mock_sleep_fn(delay, *args, **kwargs):
        sleep_calls.append(delay)
        if delay == 0.01:
            await original_sleep(0.01)

    # Patch SessionLocal and asyncio.sleep to run instantly and record delays
    with (
        patch("app.orchestrator.worker.SessionLocal", new=mock_factory),
        patch("asyncio.sleep", new=mock_sleep_fn),
    ):
        await worker._poll_mock("2")

        # Give small tick for scheduled task
        await asyncio.sleep(0.01)

    # Verify backoff sleep was scheduled
    delays = [d for d in sleep_calls if d != 0.01]
    assert len(delays) == 1
    scheduled_delay = delays[0]

    # For retries=1: initial_backoff (5) * (2 ** 1) * jitter [0.8, 1.2]
    # = 10 * [0.8, 1.2] = [8.0, 12.0]
    assert 8.0 <= scheduled_delay <= 12.0

    # Verify task was re-queued with incremented retry_count
    assert queue.qsize() == 1
    requeued_payload = await queue.get()
    assert requeued_payload["retry_count"] == 2
    assert requeued_payload["run_id"] == run_id


@pytest.mark.asyncio
async def test_dlq_escalation_after_max_retries(mock_session_factory):
    """Verify run status is updated to failed and EventBridge notifies on max retries exceeded."""
    mock_factory, session = mock_session_factory

    run_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    payload = {
        "run_id": run_id,
        "organization_id": org_id,
        "pillar": "3",
        "step_id": "coder.scaffold",
        "agent_id": "coder",
        "retry_count": 4,  # This is the 5th attempt (retry_count == 4)
    }

    async def failing_grpc_dispatcher(pl):
        raise RuntimeError("Transient worker failure")
        yield

    engine = AsyncMock()
    worker = SQSPillarWorker(
        engine=engine,
        redis=None,
        mock_grpc_dispatcher=failing_grpc_dispatcher,
    )

    queue = get_mock_pillar_queue("3")
    while not queue.empty():
        queue.get_nowait()
    await queue.put(payload)

    with patch("app.orchestrator.worker.SessionLocal", new=mock_factory):
        await worker._poll_mock("3")

    # Verify run is marked as failed via engine._update_run_status
    engine._update_run_status.assert_called_once_with(run_id, org_id, "failed")

    # Verify event published to EventBridge mock log
    log = get_event_log()
    assert len(log) == 1
    event = log[0]
    assert event["event_type"] == "agent.failed"
    assert event["organization_id"] == org_id
    assert event["run_id"] == run_id
    assert event["pillar"] == 3
    assert event["payload"]["step_id"] == "coder.scaffold"
    assert event["payload"]["agent_id"] == "coder"
    assert event["payload"]["error"] == "Max retries exceeded"

    # Queue should be empty (escalated, not re-queued)
    assert queue.empty()
