"""Artifact persistence for AF-042 — report + raw scan JSON via UDAL object store.

Mirrors ``app.agents.product_planner.persistence``: best-effort uploads that
return a URI (or None) and never raise into the graph.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.reviewer.schema import SecurityFinding

logger = logging.getLogger("app.agents.reviewer.persistence")


async def _upload(udal: Any, path: str, data: bytes, content_type: str) -> str | None:
    try:
        uri: str = await udal.object().upload(path, data, content_type)
        return uri
    except Exception as exc:  # noqa: BLE001 - persistence is best-effort
        logger.warning("Reviewer artifact upload failed for %s: %s", path, exc)
        return None


async def persist_report(
    udal: Any,
    *,
    run_id: str,
    org_id: str,
    markdown: str,
    findings: list[SecurityFinding],
) -> str | None:
    """Upload the Markdown report + raw scan JSON. Returns the report URI."""
    base = f"reviews/{org_id}/{run_id}"
    report_uri = await _upload(udal, f"{base}/report.md", markdown.encode("utf-8"), "text/markdown")
    scan_json = json.dumps([f.model_dump(mode="json") for f in findings], indent=2)
    await _upload(udal, f"{base}/scan.json", scan_json.encode("utf-8"), "application/json")
    if report_uri:
        logger.info("Reviewer report persisted for run %s → %s", run_id, report_uri)
    return report_uri
