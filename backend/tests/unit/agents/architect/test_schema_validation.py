"""Unit tests — schema validation (AF-040).

Tests: FeatureList, Requirement, ArchitectOutput Pydantic models.
No LLM, no DB, no platform.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.agents.architect.schema import ArchitectOutput, FeatureList, Requirement

# ---------------------------------------------------------------------------
# FeatureList
# ---------------------------------------------------------------------------


class TestFeatureList:
    def test_valid_feature_list(self, valid_feature_list):
        fl = FeatureList(**valid_feature_list)
        assert len(fl.features) == 8
        assert len(fl.integrations) == 3
        assert len(fl.pricing_tiers) == 3

    def test_empty_features_raises_fatal_error(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            FeatureList(features=[])

    def test_integrations_and_tiers_default_to_empty(self):
        fl = FeatureList(features=["Users can log in"])
        assert fl.integrations == []
        assert fl.pricing_tiers == []

    def test_features_must_be_list_of_strings(self):
        with pytest.raises(ValidationError):
            FeatureList(features=[123, 456])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# Requirement
# ---------------------------------------------------------------------------


class TestRequirement:
    def test_valid_fr(self):
        r = Requirement(id="FR-001", kind="FR", description="Users can sign up", priority="P0")
        assert r.kind == "FR"

    def test_valid_nfr(self):
        r = Requirement(id="NFR-001", kind="NFR", description="p99 < 150ms", priority="P0")
        assert r.kind == "NFR"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            Requirement(  # type: ignore[call-arg]
                id="FR-001",
                kind="FR",
                priority="P0",  # missing description
            )


# ---------------------------------------------------------------------------
# ArchitectOutput
# ---------------------------------------------------------------------------

_SAMPLE_ERD = "erDiagram\n    USER { uuid id PK\n datetime created_at\n datetime updated_at }"
_SAMPLE_OPENAPI = {
    "openapi": "3.1.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {},
}


class TestArchitectOutput:
    def test_valid_full_output(self, valid_feature_list, sample_requirements, sample_stack):
        requirements = [Requirement(**r) for r in sample_requirements]
        output = ArchitectOutput(
            run_id=uuid4(),
            organization_id="org-test",
            requirements=requirements,
            erd_mermaid=_SAMPLE_ERD,
            openapi_3_1=_SAMPLE_OPENAPI,
            stack=sample_stack,
            microservice_boundaries=["auth-module", "billing-module"],
            auth_strategy={"provider": "Supabase Auth"},
            scaling_plan={"ecs_tasks": {}},
            cost_estimate={"tiers": {"startup": {"monthly_usd": 95.0}}},
            feature_list=FeatureList(**valid_feature_list),
            approval_status="approved",
        )
        assert output.approval_status == "approved"
        assert output.feature_list.features[0].startswith("Users can")

    def test_default_approval_status_is_pending(
        self, valid_feature_list, sample_requirements, sample_stack
    ):
        requirements = [Requirement(**r) for r in sample_requirements]
        output = ArchitectOutput(
            run_id=uuid4(),
            organization_id="org-test",
            requirements=requirements,
            erd_mermaid=_SAMPLE_ERD,
            openapi_3_1={},
            stack=sample_stack,
            microservice_boundaries=[],
            auth_strategy={},
            scaling_plan={},
            cost_estimate={},
            feature_list=FeatureList(**valid_feature_list),
        )
        assert output.approval_status == "pending"
