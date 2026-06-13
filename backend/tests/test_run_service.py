"""Run service unit tests."""

import uuid

import pytest

from app.schemas.idea import IdeaCreate
from app.schemas.run import RunStatus
from app.services import run_service

ORG = "org_test"


def test_create_and_get_run() -> None:
    idea = IdeaCreate(text="A marketplace for second-hand textbooks in India.")
    run = run_service.create_run(idea, organization_id=ORG)
    assert run.status == RunStatus.queued
    assert run_service.get_run(run.id, organization_id=ORG).id == run.id


def test_get_missing_run_raises() -> None:
    with pytest.raises(run_service.RunNotFoundError):
        run_service.get_run(uuid.uuid4(), organization_id=ORG)


def test_runs_are_tenant_scoped() -> None:
    idea = IdeaCreate(text="A SaaS for restaurant inventory management.")
    run = run_service.create_run(idea, organization_id="org_a")
    with pytest.raises(run_service.RunNotFoundError):
        run_service.get_run(run.id, organization_id="org_b")
