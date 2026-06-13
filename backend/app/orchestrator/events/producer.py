"""AWS EventBridge publisher client (AF-034)."""

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Thread-safe in-memory log for local testing and debugging
_event_log: list[dict[str, Any]] = []


def get_event_log() -> list[dict[str, Any]]:
    """Return in-memory log of published events (test helper)."""
    return _event_log


def clear_event_log() -> None:
    """Clear the in-memory event log."""
    _event_log.clear()


class EventBridgeProducer:
    """Publishes platform events to AWS EventBridge."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        self._initialized = False

    def _init_client(self) -> None:
        """Lazily initialize boto3 client to avoid AWS dependency during imports."""
        if self._initialized:
            return

        # Only initialize real AWS client if EventBus name is configured and
        # not in dev/test fallback
        if self.settings.eventbridge_bus_name and self.settings.sqs_gate_decisions_queue_url:
            try:
                self._client = boto3.client("events", region_name=self.settings.aws_region)
            except (BotoCoreError, ClientError) as e:
                logger.warning(
                    "Failed to initialize boto3 events client: %s. Falling back to mock/dev mode.",
                    e,
                )
                self._client = None
        self._initialized = True

    async def publish_event(
        self,
        event_type: str,
        organization_id: str,
        run_id: str,
        pillar: int | None,
        payload: dict[str, Any],
    ) -> None:
        """Publish an event to AWS EventBridge (or mock log in dev)."""
        self._init_client()

        event_id = str(uuid.uuid4())
        emitted_at = datetime.now(UTC).isoformat()

        # Build payload detail matching LLD spec
        detail = {
            "schema_version": "1.0",
            "organization_id": organization_id,
            "run_id": run_id,
            "pillar": str(pillar) if pillar is not None else None,
            "agent_id": "orchestrator",
            "model": "system",
            "env": self.settings.app_env,
            "payload": payload,
            "emitted_at": emitted_at,
        }

        # Build EventBridge PutEvents request entry
        entry = {
            "Source": "autofounder.platform",
            "DetailType": event_type,
            "Detail": json.dumps(detail),
            "EventBusName": self.settings.eventbridge_bus_name,
        }

        # Save to debug log
        _event_log.append(
            {
                "event_id": event_id,
                "event_type": event_type,
                "organization_id": organization_id,
                "run_id": run_id,
                "pillar": pillar,
                "payload": payload,
                "detail": detail,
                "emitted_at": emitted_at,
            }
        )

        logger.info(
            "EventBridge event queued locally: id=%s, type=%s, run=%s",
            event_id,
            event_type,
            run_id,
        )

        if self._client:
            try:
                response = self._client.put_events(Entries=[entry])
                failed_count = response.get("FailedEntryCount", 0)
                if failed_count > 0:
                    errors = response.get("Entries", [])
                    logger.error(
                        "EventBridge PutEvents failed for %d entries: %s", failed_count, errors
                    )
                else:
                    logger.info("Successfully published event %s to EventBridge", event_id)
            except (BotoCoreError, ClientError) as e:
                logger.error("Failed to publish event to AWS EventBridge: %s", e)
        else:
            logger.info("Mock event published: %s", json.dumps(entry, indent=2))
            if event_type == "run.created":
                import asyncio
                from app.orchestrator.events.consumer import get_mock_run_created_queue

                asyncio.create_task(get_mock_run_created_queue().put(detail))


# Global producer singleton
event_producer = EventBridgeProducer()
