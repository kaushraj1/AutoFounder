"""SQS consumer for gate decisions (AF-034)."""

import asyncio
import json
import logging
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Mock queue for in-memory testing
_mock_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()


def get_mock_queue() -> asyncio.Queue[dict[str, Any]]:
    """Return the mock queue for local test injection."""
    return _mock_queue


class SQSGateDecisionConsumer:
    """Consumes gate decision messages from SQS to resume runs asynchronously."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self.settings = get_settings()
        self._client: Any = None
        self._initialized = False

    def _init_client(self) -> None:
        if self._initialized:
            return
        if self.settings.sqs_gate_decisions_queue_url:
            try:
                self._client = boto3.client("sqs", region_name=self.settings.aws_region)
            except (BotoCoreError, ClientError) as e:
                logger.warning(
                    "Failed to initialize boto3 SQS client: %s. Using in-memory fallback.", e
                )
                self._client = None
        self._initialized = True

    async def start(self) -> None:
        """Start the consumer loop."""
        logger.info("Starting SQS Gate Decision Consumer...")
        self._init_client()

        try:
            while True:
                if self._client and self.settings.sqs_gate_decisions_queue_url:
                    await self._poll_aws()
                else:
                    await self._poll_mock()
        except asyncio.CancelledError:
            logger.info("SQS Gate Decision Consumer stopped.")
            raise

    async def _poll_aws(self) -> None:
        if not self._client:
            return
        try:
            # SQS Long polling
            response = self._client.receive_message(
                QueueUrl=self.settings.sqs_gate_decisions_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=self.settings.sqs_poll_wait_time_seconds,
            )
            messages = response.get("Messages", [])
            for msg in messages:
                body = msg.get("Body", "")
                receipt_handle = msg.get("ReceiptHandle", "")

                try:
                    payload = json.loads(body)
                    # Support SNS-wrapped messages
                    if "Message" in payload and isinstance(payload["Message"], str):
                        payload = json.loads(payload["Message"])

                    await self._process_message(payload)

                    # Delete message from SQS on successful processing
                    self._client.delete_message(
                        QueueUrl=self.settings.sqs_gate_decisions_queue_url,
                        ReceiptHandle=receipt_handle,
                    )
                except Exception as e:
                    logger.error("Error processing SQS message: %s", e, exc_info=True)
                    # Don't delete the message on failure to allow retry/DLQ fallback
        except Exception as e:
            logger.error("SQS receive_message error: %s", e)
            await asyncio.sleep(5)  # Wait before retrying on general errors

    async def _poll_mock(self) -> None:
        try:
            # Long poll the in-memory mock queue with a timeout
            payload = await asyncio.wait_for(_mock_queue.get(), timeout=1.0)
            try:
                await self._process_message(payload)
            except Exception as e:
                logger.error("Error processing mock message: %s", e)
            finally:
                _mock_queue.task_done()
        except TimeoutError:
            pass

    async def _process_message(self, payload: dict[str, Any]) -> None:
        run_id = payload.get("run_id")
        gate_decision = payload.get("decision")
        pivot_text = payload.get("pivot_text")

        if not run_id or not gate_decision:
            logger.error("Invalid gate decision message payload: %s", payload)
            return

        logger.info(
            "SQS Consumer resuming run: run=%s, decision=%s, pivot=%s",
            run_id,
            gate_decision,
            pivot_text is not None,
        )

        await self.engine.resume(
            run_id=str(run_id),
            gate_decision=gate_decision,
            pivot_text=pivot_text,
        )


# Mock queue for run.created in-memory testing
_mock_run_created_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()


def get_mock_run_created_queue() -> asyncio.Queue[dict[str, Any]]:
    """Return the mock queue for run.created event injection."""
    return _mock_run_created_queue


class SQSRunCreatedConsumer:
    """Consumes run.created messages from SQS to start runs asynchronously."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self.settings = get_settings()
        self._client: Any = None
        self._initialized = False

    def _init_client(self) -> None:
        if self._initialized:
            return
        if self.settings.sqs_run_created_queue_url:
            try:
                self._client = boto3.client("sqs", region_name=self.settings.aws_region)
            except (BotoCoreError, ClientError) as e:
                logger.warning(
                    "Failed to initialize boto3 SQS client for run creation: %s. Using in-memory fallback.",
                    e,
                )
                self._client = None
        self._initialized = True

    async def start(self) -> None:
        """Start the consumer loop."""
        logger.info("Starting SQS Run Created Consumer...")
        self._init_client()

        try:
            while True:
                if self._client and self.settings.sqs_run_created_queue_url:
                    await self._poll_aws()
                else:
                    await self._poll_mock()
        except asyncio.CancelledError:
            logger.info("SQS Run Created Consumer stopped.")
            raise

    async def _poll_aws(self) -> None:
        if not self._client:
            return
        try:
            response = self._client.receive_message(
                QueueUrl=self.settings.sqs_run_created_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=self.settings.sqs_poll_wait_time_seconds,
            )
            messages = response.get("Messages", [])
            for msg in messages:
                body = msg.get("Body", "")
                receipt_handle = msg.get("ReceiptHandle", "")

                try:
                    payload = json.loads(body)
                    if "Message" in payload and isinstance(payload["Message"], str):
                        payload = json.loads(payload["Message"])

                    await self._process_message(payload)

                    self._client.delete_message(
                        QueueUrl=self.settings.sqs_run_created_queue_url,
                        ReceiptHandle=receipt_handle,
                    )
                except Exception as e:
                    logger.error("Error processing SQS run created message: %s", e, exc_info=True)
        except Exception as e:
            logger.error("SQS run created receive_message error: %s", e)
            await asyncio.sleep(5)

    async def _poll_mock(self) -> None:
        try:
            payload = await asyncio.wait_for(_mock_run_created_queue.get(), timeout=1.0)
            try:
                await self._process_message(payload)
            except Exception as e:
                logger.error("Error processing mock run created message: %s", e)
            finally:
                _mock_run_created_queue.task_done()
        except TimeoutError:
            pass

    async def _process_message(self, payload: dict[str, Any]) -> None:
        event_payload = payload.get("payload", {})
        run_id = payload.get("run_id")
        organization_id = payload.get("organization_id")
        workspace_id = event_payload.get("workspace_id")
        idea_text = event_payload.get("idea_text")

        if not all([run_id, organization_id, workspace_id, idea_text]):
            logger.error("Invalid run created message payload: %s", payload)
            return

        logger.info(
            "SQS Consumer starting run: run=%s, org=%s, workspace=%s",
            run_id,
            organization_id,
            workspace_id,
        )

        from app.orchestrator.state import make_initial_state

        initial = make_initial_state(
            run_id=str(run_id),
            organization_id=str(organization_id),
            workspace_id=str(workspace_id),
            idea_text=str(idea_text),
            idea_meta={},
        )
        config = self.engine._config(run_id)
        await self.engine._get_graph().ainvoke(initial, config)
        await self.engine._sync_status_from_graph(run_id, organization_id)
