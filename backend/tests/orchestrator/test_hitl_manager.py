"""Tests for HITL Gate Manager & Event Processing (AF-034)."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.gate import Gate
from app.orchestrator.events.consumer import SQSGateDecisionConsumer, get_mock_queue
from app.orchestrator.events.producer import clear_event_log, event_producer, get_event_log
from app.orchestrator.hitl.gate_manager import check_and_create_gate, check_gate_timeouts
from app.orchestrator.hitl.notifier import emit_gate_required


@pytest.fixture(autouse=True)
def setup_teardown_event_log():
    """Ensure event log is clean for every test."""
    clear_event_log()
    yield
    clear_event_log()


@pytest.mark.asyncio
async def test_eventbridge_producer_mock_publishing():
    """Verify EventBridgeProducer pushes formatted events to local log in dev/test mode."""
    org_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    payload = {"test_key": "test_val"}

    await event_producer.publish_event(
        event_type="test.event",
        organization_id=org_id,
        run_id=run_id,
        pillar=1,
        payload=payload,
    )

    log = get_event_log()
    assert len(log) == 1
    event = log[0]

    assert event["event_type"] == "test.event"
    assert event["organization_id"] == org_id
    assert event["run_id"] == run_id
    assert event["pillar"] == 1
    assert event["payload"] == payload

    # Check detail envelope layout
    detail = event["detail"]
    assert detail["schema_version"] == "1.0"
    assert detail["organization_id"] == org_id
    assert detail["run_id"] == run_id
    assert detail["pillar"] == "1"
    assert detail["env"] == "development"
    assert detail["payload"] == payload
    assert "emitted_at" in detail


@pytest.mark.asyncio
async def test_emit_gate_required():
    """Verify emit_gate_required correctly calls the event producer with gate.required shape."""
    run_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    gate_id = str(uuid.uuid4())
    display_data = {"viability_score": 75}
    timeout_at = datetime.now(UTC) + timedelta(hours=24)

    await emit_gate_required(
        run_id=run_id,
        org_id=org_id,
        pillar=1,
        gate_id=gate_id,
        kind="validation_approve",
        display_data=display_data,
        timeout_at=timeout_at,
    )

    log = get_event_log()
    assert len(log) == 1
    event = log[0]

    assert event["event_type"] == "gate.required"
    assert event["payload"]["gate_id"] == gate_id
    assert event["payload"]["kind"] == "validation_approve"
    assert event["payload"]["display_data"] == display_data
    assert event["payload"]["timeout_at"] == timeout_at.isoformat()


@pytest.mark.asyncio
async def test_check_and_create_gate_new():
    """Verify that when a graph is paused, a Gate record is inserted,
    and a notify event is published.
    """
    run_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())

    # Mock DB Session
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_execute_result

    # Mock LangGraph Snapshot
    snapshot = MagicMock()
    snapshot.next = ["validation_gate"]
    snapshot.values = {
        "current_pillar": 1,
        "strategy_output": {"viability_score": 88, "lean_canvas": {}},
    }

    # Mock Graph and Config
    mock_graph = AsyncMock()
    config = {"configurable": {"thread_id": run_id}}

    # Call
    await check_and_create_gate(
        run_id=run_id,
        org_id=org_id,
        snapshot=snapshot,
        db_session=mock_session,
        graph=mock_graph,
        config=config,
    )

    # Asserts
    # Query check was executed
    assert mock_session.execute.call_count == 1

    # DB add and commit was called
    assert mock_session.add.call_count == 1
    assert mock_session.commit.call_count == 1

    # Verify model fields added
    added_gate = mock_session.add.call_args[0][0]
    assert isinstance(added_gate, Gate)
    assert added_gate.run_id == uuid.UUID(run_id)
    assert added_gate.organization_id == uuid.UUID(org_id)
    assert added_gate.kind == "validation_approve"
    assert added_gate.state == "pending"
    assert added_gate.payload == {"viability_score": 88, "lean_canvas": {}}
    assert added_gate.timeout_at is not None

    # Graph state updated with active_gate_id
    assert mock_graph.aupdate_state.call_count == 1
    update_data = mock_graph.aupdate_state.call_args[0][1]
    assert "active_gate_id" in update_data
    assert update_data["active_gate_id"] == str(added_gate.id)

    # Notified
    log = get_event_log()
    assert len(log) == 1
    assert log[0]["event_type"] == "gate.required"
    assert log[0]["payload"]["gate_id"] == str(added_gate.id)


@pytest.mark.asyncio
async def test_check_and_create_gate_existing():
    """Verify that if a pending gate already exists, it is not recreated
    but graph state is synced.
    """
    run_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())

    existing_gate = Gate(
        id=uuid.uuid4(),
        run_id=uuid.UUID(run_id),
        organization_id=uuid.UUID(org_id),
        kind="validation_approve",
        state="pending",
    )

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = existing_gate
    mock_session.execute.return_value = mock_execute_result

    snapshot = MagicMock()
    snapshot.next = ["validation_gate"]
    snapshot.values = {"active_gate_id": None}

    mock_graph = AsyncMock()
    config = {"configurable": {"thread_id": run_id}}

    await check_and_create_gate(
        run_id=run_id,
        org_id=org_id,
        snapshot=snapshot,
        db_session=mock_session,
        graph=mock_graph,
        config=config,
    )

    # DB add not called because it exists
    assert mock_session.add.call_count == 0
    # Graph updated to sync active_gate_id
    assert mock_graph.aupdate_state.call_count == 1
    assert mock_graph.aupdate_state.call_args[0][1]["active_gate_id"] == str(existing_gate.id)


@pytest.mark.asyncio
async def test_check_gate_timeouts():
    """Verify check_gate_timeouts flags timed out gates and calls resume on the engine."""
    mock_session = AsyncMock()

    gate1 = Gate(
        id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        kind="validation_approve",
        state="pending",
        timeout_at=datetime.now(UTC) - timedelta(minutes=10),
    )

    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value.all.return_value = [gate1]
    mock_session.execute.return_value = mock_execute_result

    mock_engine = AsyncMock()

    await check_gate_timeouts(mock_session, mock_engine)

    # Gate is marked timed_out
    assert gate1.state == "timed_out"
    assert mock_session.commit.call_count == 1

    # Engine resume triggered
    mock_engine.resume.assert_awaited_once_with(str(gate1.run_id), gate_decision="timed_out")


@pytest.mark.asyncio
async def test_sqs_consumer_mock_polling():
    """Verify SQSGateDecisionConsumer processes events from queue and triggers resume."""
    mock_engine = AsyncMock()
    consumer = SQSGateDecisionConsumer(mock_engine)

    run_id = str(uuid.uuid4())
    gate_id = str(uuid.uuid4())
    message = {
        "run_id": run_id,
        "gate_id": gate_id,
        "decision": "approved",
        "pivot_text": "new pivot text",
    }

    # Inject message to mock queue
    queue = get_mock_queue()
    queue.put_nowait(message)

    # Start consumer as background task
    task = asyncio.create_task(consumer.start())

    # Wait briefly for execution
    await asyncio.sleep(0.1)

    # Stop consumer
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Assert engine resume was triggered
    mock_engine.resume.assert_awaited_once_with(
        run_id=run_id,
        gate_decision="approved",
        pivot_text="new pivot text",
    )
