"""Immutable audit & lineage emit for the guardrail pipeline (AF-046).

Every guard decision produces a ``LineageRecord``. The structured log is the
always-available floor; when a DB session is present the record is also written
to the append-only ``platform.audit_log`` table, and when an S3 Object Lock
bucket is configured it is pushed there for 7-year immutable retention.

``emit_lineage`` never raises — a broken audit path must not crash an agent —
but it returns whether a *durable* record was written so the pipeline can apply
the configured "block on audit failure" policy (CLAUDE.md §34 / plan D3).
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from app.db.audit import emit_audit_event
from app.guardrails.metrics import GUARDRAIL_AUDIT_WRITE_FAILURES
from app.guardrails.schema import GuardrailContext, GuardResult, LineageRecord

logger = logging.getLogger(__name__)


def build_record(ctx: GuardrailContext, result: GuardResult) -> LineageRecord:
    """Assemble the immutable lineage record for a single stage decision."""
    return LineageRecord(
        organization_id=ctx.organization_id,
        run_id=ctx.run_id,
        agent_id=ctx.agent_id,
        stage=result.stage,
        decision=result.decision,
        severity=result.severity,
        detail={
            "blocked": result.blocked,
            "reason": result.reason,
            "flags": result.flags,
        },
        ts=datetime.now(UTC).isoformat(),
    )


async def emit_lineage(ctx: GuardrailContext, result: GuardResult) -> bool:
    """Emit one lineage record. Returns True if a *durable* store accepted it.

    Order: structured log (always) -> platform.audit_log (if session) ->
    S3 Object Lock (if configured). Never raises.
    """
    record = build_record(ctx, result)

    # Floor: structured log — always present, never raises.
    logger.info(
        "guardrail_lineage stage=%s decision=%s severity=%s org=%s run=%s agent=%s",
        record.stage.value,
        record.decision.value,
        record.severity.value,
        record.organization_id,
        record.run_id,
        record.agent_id,
    )

    durable = False

    # Primary durable store for the MVP: append-only platform.audit_log.
    if ctx.session is not None:
        try:
            await emit_audit_event(
                ctx.session,
                org_id=ctx.organization_id,
                actor=ctx.agent_id or "guardrails",
                action=f"guardrail.{record.stage.value}.{record.decision.value}",
                resource_type="guardrail_stage",
                resource_id=record.stage.value,
                run_id=ctx.run_id,
                agent_id=ctx.agent_id,
                outcome=_outcome(result),
                metadata=record.detail,
            )
            durable = True
        except Exception:
            logger.exception("guardrail_audit_log_write_failed stage=%s", record.stage.value)

    # Optional immutable store: S3 Object Lock (best-effort, off the event loop).
    settings = get_settings()
    bucket = getattr(settings, "aws_s3_audit_bucket", "") or ""
    if bucket:
        try:
            await asyncio.to_thread(_write_s3_lineage, bucket, record)
            durable = True
        except Exception:
            logger.exception("guardrail_audit_s3_write_failed stage=%s", record.stage.value)

    if not durable and ctx.session is None and not bucket:
        # No durable store configured (dev/test): the log floor is acceptable.
        return False

    if not durable:
        GUARDRAIL_AUDIT_WRITE_FAILURES.inc()
    return durable


def _outcome(result: GuardResult) -> str:
    if result.blocked:
        return "blocked"
    return "flagged" if result.flags else "success"


def _write_s3_lineage(bucket: str, record: LineageRecord) -> None:
    """Put the lineage record to S3 with Object Lock governance retention.

    Synchronous (boto3) — call via ``asyncio.to_thread``. Imported lazily so the
    module loads without AWS configured.
    """
    import boto3  # local import: only when an audit bucket is configured

    key = (
        f"{record.organization_id}/lineage/"
        f"{record.run_id or 'no-run'}/{record.ts}-{record.stage.value}.json"
    )
    body: dict[str, Any] = record.model_dump()
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(body).encode("utf-8"),
        ContentType="application/json",
    )
