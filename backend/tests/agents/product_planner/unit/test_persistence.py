"""T10 + T12-T13 — PRD markdown rendering and persistence."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.product_planner.persistence import persist_prd, render_prd_markdown
from app.agents.product_planner.schema import (
    PRD,
    Milestone,
    ProductPlannerOutput,
    Requirement,
    UserStory,
)


def _make_output() -> ProductPlannerOutput:
    return ProductPlannerOutput(
        run_id="run-001",
        organization_id="org-001",
        domain="B2B SaaS",
        prd=PRD(
            title="TeamSync",
            overview="AI scheduling for remote teams.",
            problem_statement="Remote teams waste hours scheduling.",
            goals=["Reduce friction by 80%"],
            non_goals=["Replace video calls"],
            target_users=["Alex Chen"],
            success_metrics=["50% fewer emails"],
            scope_in=["Calendar sync"],
            scope_out=["Video calls"],
        ),
        requirements=[
            Requirement(
                id="FR-001",
                kind="functional",
                statement="Sync calendars.",
                priority="must",
                traces_to="Calendar sync",
            )
        ],
        user_stories=[
            UserStory(
                id="US-001",
                persona="Alex Chen",
                role="EM",
                want="sync calendar",
                benefit="save time",
                acceptance_criteria=["It syncs within 2s"],
                priority="must",
                epic="Calendar Sync",
            )
        ],
        roadmap=[
            Milestone(
                phase="MVP",
                title="Core Scheduling",
                objective="Ship basic sync.",
                epics=["Calendar Sync"],
                user_story_ids=["US-001"],
                target_weeks=8,
            )
        ],
        prd_markdown="",
        coverage_score=0.85,
        confidence="high",
    )


def test_render_contains_all_ids() -> None:
    output = _make_output()
    md = render_prd_markdown(output)
    assert "FR-001" in md
    assert "US-001" in md
    assert "MVP" in md


def test_render_contains_prd_title() -> None:
    output = _make_output()
    md = render_prd_markdown(output)
    assert "TeamSync" in md


def test_render_is_deterministic() -> None:
    output = _make_output()
    assert render_prd_markdown(output) == render_prd_markdown(output)


def test_render_contains_coverage() -> None:
    output = _make_output()
    md = render_prd_markdown(output)
    assert "0.85" in md
    assert "high" in md


@pytest.mark.asyncio
async def test_persist_returns_uri_on_success() -> None:
    udal = MagicMock()
    obj = MagicMock()
    obj.upload = AsyncMock(return_value="https://storage.example.com/prd.md")
    udal.object = MagicMock(return_value=obj)

    uri = await persist_prd(udal, run_id="run-001", org_id="org-001", markdown="# PRD")
    assert uri == "https://storage.example.com/prd.md"
    obj.upload.assert_called_once()


@pytest.mark.asyncio
async def test_persist_returns_none_on_failure() -> None:
    udal = MagicMock()
    obj = MagicMock()
    obj.upload = AsyncMock(side_effect=RuntimeError("S3 unavailable"))
    udal.object = MagicMock(return_value=obj)

    uri = await persist_prd(udal, run_id="run-001", org_id="org-001", markdown="# PRD")
    assert uri is None
