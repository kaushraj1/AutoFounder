"""Run service — creates and reads validation runs.

Phase 1 uses a tenant-partitioned in-memory store so the API and tests work with no database.
Sprint 1 swaps ``_STORE`` for UDAL-backed persistence (the ``Run`` model and Alembic schema
already exist) and kicks off the LangGraph orchestrator.
"""

import uuid
from datetime import UTC, datetime

from app.schemas.idea import IdeaCreate
from app.schemas.run import RunRead, RunStatus

# organization_id -> {run_id -> RunRead}. Tenant-partitioned by key, mirroring production isolation.
_STORE: dict[str, dict[uuid.UUID, RunRead]] = {}


class RunNotFoundError(Exception):
    """Raised when a run id does not exist for the given organization."""


def create_run(idea: IdeaCreate, *, organization_id: str) -> RunRead:
    """Create a new validation run for the submitted idea."""
    # idea.text is validated by the schema; Sprint 1 passes it to the orchestrator.
    _ = idea.text
    run = RunRead(
        id=uuid.uuid4(),
        pillar="strategy",
        status=RunStatus.queued,
        created_at=datetime.now(UTC),
    )
    _STORE.setdefault(organization_id, {})[run.id] = run
    return run


def get_run(run_id: uuid.UUID, *, organization_id: str) -> RunRead:
    """Return a run by id, scoped to the organization."""
    try:
        return _STORE[organization_id][run_id]
    except KeyError as exc:
        raise RunNotFoundError(str(run_id)) from exc


def list_runs(*, organization_id: str) -> list[RunRead]:
    """List all runs for the organization."""
    return list(_STORE.get(organization_id, {}).values())


def _reset_store() -> None:
    """Test helper — clear the in-memory store."""
    _STORE.clear()
