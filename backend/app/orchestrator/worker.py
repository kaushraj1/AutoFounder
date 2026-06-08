"""SQS consumer and task dispatcher for execution pillars (AF-035)."""

import asyncio
import json
import logging
import random
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import text

from app.core.config import get_settings
from app.core.security import Principal
from app.db.session import SessionLocal
from app.db.udal import UDAL
from app.orchestrator.events.producer import event_producer

logger = logging.getLogger(__name__)

# Mock queues for in-memory testing per pillar (1 to 7)
_mock_pillar_queues: dict[str, asyncio.Queue[dict[str, Any]]] = {
    str(i): asyncio.Queue() for i in range(1, 8)
}


def get_mock_pillar_queue(pillar: str) -> asyncio.Queue[dict[str, Any]]:
    """Return the mock queue for the specified pillar (test helper)."""
    p_str = str(pillar)
    if p_str not in _mock_pillar_queues:
        _mock_pillar_queues[p_str] = asyncio.Queue()
    return _mock_pillar_queues[p_str]


class SQSPillarWorker:
    """Monitors pillar tasks, dispatches them to Agent Workers via gRPC, and logs events."""

    def __init__(
        self,
        engine: Any,
        redis: Any = None,
        mock_grpc_dispatcher: Any = None,
    ) -> None:
        self.engine = engine
        self._redis = redis
        self._mock_grpc_dispatcher = mock_grpc_dispatcher
        self.settings = get_settings()
        self._client: Any = None
        self._initialized = False
        self._tasks: list[asyncio.Task] = []

    def _init_client(self) -> None:
        """Lazily initialize boto3 SQS client."""
        if self._initialized:
            return
        if self.settings.sqs_pillar_queues:
            try:
                self._client = boto3.client("sqs", region_name=self.settings.aws_region)
            except (BotoCoreError, ClientError) as e:
                logger.warning(
                    "Failed to initialize boto3 SQS client for worker: %s. Using mock fallback.",
                    e,
                )
                self._client = None
        self._initialized = True

    async def start(self) -> None:
        """Start the polling loop for all 7 execution pillars."""
        logger.info("Starting SQS Pillar Worker...")
        self._init_client()

        pillars = [str(i) for i in range(1, 8)]
        self._tasks = []
        try:
            for pillar in pillars:
                task = asyncio.create_task(self._poll_loop(pillar))
                self._tasks.append(task)
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            logger.info("SQS Pillar Worker start was cancelled. Stopping loops...")
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
            raise

    async def _poll_loop(self, pillar: str) -> None:
        """Infinite polling loop for a specific pillar queue."""
        logger.info("Pillar %s polling loop started.", pillar)
        queue_url = self.settings.sqs_pillar_queues.get(pillar)

        while True:
            try:
                if self._client and queue_url:
                    await self._poll_aws(pillar, queue_url)
                else:
                    await self._poll_mock(pillar)
            except asyncio.CancelledError:
                logger.info("Pillar %s polling loop stopped.", pillar)
                raise
            except Exception as e:
                logger.error(
                    "Exception in pillar %s polling loop: %s",
                    pillar,
                    e,
                    exc_info=True,
                )
                await asyncio.sleep(5)  # Backoff before retrying on general loop error

    async def _poll_aws(self, pillar: str, queue_url: str) -> None:
        if not self._client:
            return
        try:
            response = await asyncio.to_thread(
                self._client.receive_message,
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=self.settings.sqs_poll_wait_time_seconds,
                AttributeNames=["ApproximateReceiveCount"],
            )
            messages = response.get("Messages", [])
            for msg in messages:
                body = msg.get("Body", "")
                receipt_handle = msg.get("ReceiptHandle", "")

                try:
                    payload = json.loads(body)
                    if "Message" in payload and isinstance(payload["Message"], str):
                        payload = json.loads(payload["Message"])

                    receive_count = int(msg.get("Attributes", {}).get("ApproximateReceiveCount", 1))

                    await self._process_task(payload, retries=receive_count - 1)

                    # Delete message on success
                    await asyncio.to_thread(
                        self._client.delete_message,
                        QueueUrl=queue_url,
                        ReceiptHandle=receipt_handle,
                    )
                except Exception as e:
                    logger.error(
                        "Error processing SQS message on pillar %s: %s",
                        pillar,
                        e,
                        exc_info=True,
                    )
                    # Temporary failure: exponential backoff + jitter or DLQ escalation
                    receive_count = int(msg.get("Attributes", {}).get("ApproximateReceiveCount", 1))
                    await self._handle_failure(
                        pillar=pillar,
                        payload=payload if "payload" in locals() else {},
                        retries=receive_count - 1,
                        queue_url=queue_url,
                        receipt_handle=receipt_handle,
                    )
        except Exception as e:
            logger.error("SQS receive_message error on pillar %s: %s", pillar, e)
            await asyncio.sleep(5)

    async def _poll_mock(self, pillar: str) -> None:
        mock_queue = get_mock_pillar_queue(pillar)
        try:
            payload = await asyncio.wait_for(mock_queue.get(), timeout=1.0)
            retries = payload.get("retry_count", 0)
            try:
                await self._process_task(payload, retries=retries)
            except Exception as e:
                logger.error("Error processing mock message on pillar %s: %s", pillar, e)
                await self._handle_failure(
                    pillar=pillar,
                    payload=payload,
                    retries=retries,
                )
            finally:
                mock_queue.task_done()
        except TimeoutError:
            pass

    async def _process_task(self, payload: dict[str, Any], retries: int) -> None:
        run_id = payload.get("run_id")
        organization_id = payload.get("organization_id") or payload.get("org_id")
        pillar = str(payload.get("pillar"))
        step_id = payload.get("step_id")
        agent_id = payload.get("agent_id")

        if not all([run_id, organization_id, pillar, step_id, agent_id]):
            logger.error("Invalid task message payload: %s", payload)
            raise ValueError(f"Missing required fields in payload: {payload}")

        logger.info(
            "SQS Worker processing task: run=%s, org=%s, pillar=%s, step=%s, agent=%s",
            run_id,
            organization_id,
            pillar,
            step_id,
            agent_id,
        )

        if self._mock_grpc_dispatcher:
            events_stream = self._mock_grpc_dispatcher(payload)
        else:
            events_stream = self._grpc_dispatch(payload)

        principal = Principal(organization_id=str(organization_id), role="system")

        async with SessionLocal() as session:
            udal = UDAL(principal=principal, session=session, redis=self._redis)
            async with udal.relational() as db:
                async for event in events_stream:
                    event_type = getattr(event, "event_type", None) or event.get("event_type")
                    event_payload_raw = getattr(event, "payload", None) or event.get("payload")
                    event_timestamp = getattr(event, "timestamp", None) or event.get("timestamp")

                    if isinstance(event_payload_raw, bytes):
                        event_payload = json.loads(event_payload_raw.decode("utf-8"))
                    elif isinstance(event_payload_raw, str):
                        event_payload = json.loads(event_payload_raw)
                    else:
                        event_payload = event_payload_raw or {}

                    if event_timestamp:
                        occurred_at = datetime.fromtimestamp(event_timestamp / 1000.0, tz=UTC)
                    else:
                        occurred_at = datetime.now(UTC)

                    await db.session.execute(
                        text("""
                            INSERT INTO step_events (
                                run_id, organization_id, pillar, agent_id,
                                event_type, payload, occurred_at
                            ) VALUES (
                                CAST(:run_id AS UUID), CAST(:organization_id AS UUID), :pillar,
                                :agent_id, :event_type, CAST(:payload AS JSONB), :occurred_at
                            )
                        """),
                        {
                            "run_id": run_id,
                            "organization_id": organization_id,
                            "pillar": pillar,
                            "agent_id": agent_id,
                            "event_type": event_type,
                            "payload": json.dumps(event_payload),
                            "occurred_at": occurred_at,
                        },
                    )
                await db.session.commit()

        # Engine resumption upon successful step execution
        await self.engine.resume(run_id=str(run_id), gate_decision="approved")

    async def _grpc_dispatch(self, payload: dict[str, Any]):
        import grpc

        from app.orchestrator.agent_worker_pb2 import (
            DispatchStepRequest,
        )
        from app.orchestrator.agent_worker_pb2_grpc import AgentWorkerServiceStub

        input_bytes = json.dumps(payload.get("input", {})).encode("utf-8")
        request = DispatchStepRequest(
            run_id=str(payload["run_id"]),
            step_id=str(payload["step_id"]),
            agent_id=str(payload["agent_id"]),
            organization_id=str(payload["organization_id"]),
            input=input_bytes,
        )

        async with grpc.aio.insecure_channel(self.settings.workers_grpc_host) as channel:
            stub = AgentWorkerServiceStub(channel)
            async for event in stub.DispatchStep(request):
                yield event

    async def _handle_failure(
        self,
        pillar: str,
        payload: dict[str, Any],
        retries: int,
        queue_url: str | None = None,
        receipt_handle: str | None = None,
    ) -> None:
        run_id = payload.get("run_id")
        organization_id = payload.get("organization_id") or payload.get("org_id")
        step_id = payload.get("step_id", "unknown")
        agent_id = payload.get("agent_id", "unknown")

        max_attempts = 5
        if retries < max_attempts - 1:
            initial_backoff = 5
            jitter = random.uniform(0.8, 1.2)
            delay = min(900, initial_backoff * (2**retries) * jitter)

            logger.warning(
                "Task failed on pillar %s (attempt %d/%d). Visibility backoff: %.2fs, run_id=%s",
                pillar,
                retries + 1,
                max_attempts,
                delay,
                run_id,
            )

            if self._client and queue_url and receipt_handle:
                try:
                    await asyncio.to_thread(
                        self._client.change_message_visibility,
                        QueueUrl=queue_url,
                        ReceiptHandle=receipt_handle,
                        VisibilityTimeout=int(delay),
                    )
                except Exception as e:
                    logger.error("Failed to change SQS message visibility: %s", e)
            else:
                # Mock mode: schedule retry re-queue
                async def re_queue_with_delay() -> None:
                    await asyncio.sleep(delay)
                    mock_payload = payload.copy()
                    mock_payload["retry_count"] = retries + 1
                    await get_mock_pillar_queue(pillar).put(mock_payload)

                asyncio.create_task(re_queue_with_delay())
        else:
            logger.error(
                "Task failed on pillar %s after %d attempts. Escalating to DLQ for run_id=%s",
                pillar,
                max_attempts,
                run_id,
            )

            if self._client and queue_url and receipt_handle:
                try:
                    await asyncio.to_thread(
                        self._client.delete_message,
                        QueueUrl=queue_url,
                        ReceiptHandle=receipt_handle,
                    )
                except Exception as e:
                    logger.error("Failed to delete failed message from primary SQS queue: %s", e)

            # Mark run as failed
            if run_id and organization_id:
                try:
                    await self.engine._update_run_status(
                        str(run_id), str(organization_id), "failed"
                    )
                except Exception as e:
                    logger.error("Failed to update run status to failed in DB: %s", e)

                # Publish agent.failed to EventBridge
                try:
                    await event_producer.publish_event(
                        event_type="agent.failed",
                        organization_id=str(organization_id),
                        run_id=str(run_id),
                        pillar=int(pillar) if pillar.isdigit() else None,
                        payload={
                            "step_id": step_id,
                            "agent_id": agent_id,
                            "error": "Max retries exceeded",
                        },
                    )
                except Exception as e:
                    logger.error("Failed to publish agent.failed to EventBridge: %s", e)
