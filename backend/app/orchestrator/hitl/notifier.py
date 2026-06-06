"""Notifier for HITL gate events (AF-034)."""

import logging
from datetime import datetime

from app.orchestrator.events.producer import event_producer

logger = logging.getLogger(__name__)


async def emit_gate_required(
    run_id: str,
    org_id: str,
    pillar: int,
    gate_id: str,
    kind: str,
    display_data: dict,
    timeout_at: datetime | None = None,
) -> None:
    """Emit a gate.required event to EventBridge."""
    payload = {
        "gate_id": gate_id,
        "kind": kind,
        "display_data": display_data,
        "timeout_at": timeout_at.isoformat() if timeout_at else None,
    }

    logger.info("Emitting gate.required event for run=%s, gate=%s (%s)", run_id, gate_id, kind)

    await event_producer.publish_event(
        event_type="gate.required",
        organization_id=org_id,
        run_id=run_id,
        pillar=pillar,
        payload=payload,
    )
