"""Integration test — happy path: PRD → full architecture → approved (AF-040).

The full graph runs end-to-end with FakeLLM (no real Gemini calls).
Verifies that all 9 nodes produce correct output and ArchitectOutput
can be constructed from the final state.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agents.architect.graph import build_architect_graph
from app.agents.architect.schema import ArchitectOutput, FeatureList, Requirement
from tests.integration.agents.architect.fake_llm import patch_llm

_FIXTURES_DIR = Path(__file__).parent.parent.parent.parent.parent / "app/agents/architect/fixtures"


@pytest.fixture()
def saas_fixture() -> dict:
    return json.loads((_FIXTURES_DIR / "saas_prd.json").read_text())


@pytest.fixture()
def initial_state(saas_fixture: dict) -> dict:
    return {
        "run_id": "00000000-0000-0000-0000-000000000001",
        "organization_id": "org-test",
        "idea_normalised": saas_fixture["idea_normalised"],
        "viability_band": saas_fixture["viability_band"],
        "lean_canvas": saas_fixture["lean_canvas"],
        "prd": saas_fixture["prd"],
        "approval_status": "approved",
        "errors": [],
        "llm_tokens_used": 0,
    }


class TestHappyPath:
    def test_graph_completes_without_errors(self, initial_state):
        with patch_llm():
            graph = build_architect_graph()
            result = graph.invoke(initial_state)

        assert result["errors"] == [], f"Unexpected errors: {result['errors']}"

    def test_requirements_extracted(self, initial_state):
        with patch_llm():
            result = build_architect_graph().invoke(initial_state)

        assert len(result["requirements"]) >= 5
        kinds = {r["kind"] for r in result["requirements"]}
        assert "FR" in kinds
        assert "NFR" in kinds

    def test_erd_present_and_valid(self, initial_state):
        from app.agents.architect.tools.mermaid import MermaidTool

        with patch_llm():
            result = build_architect_graph().invoke(initial_state)

        erd = result["erd_mermaid"]
        assert erd.strip().startswith("erDiagram")
        validation = MermaidTool().validate(erd)
        assert validation.valid, f"ERD invalid: {validation.errors}"

    def test_openapi_present_and_valid(self, initial_state):
        from app.agents.architect.tools.openapi_validate import OpenAPIValidateTool

        with patch_llm():
            result = build_architect_graph().invoke(initial_state)

        spec = result["openapi_3_1"]
        assert spec.get("openapi", "").startswith("3.")
        validation = OpenAPIValidateTool().validate(spec)
        assert validation.valid, f"OpenAPI invalid: {validation.errors}"

    def test_stack_has_required_keys(self, initial_state):
        with patch_llm():
            result = build_architect_graph().invoke(initial_state)

        stack = result["stack"]
        for key in ("frontend", "backend", "database"):
            assert key in stack, f"Stack missing '{key}'"

    def test_featurelist_non_empty(self, initial_state):
        with patch_llm():
            result = build_architect_graph().invoke(initial_state)

        fl = result["feature_list"]
        assert len(fl["features"]) >= 8
        assert len(fl["integrations"]) >= 2
        assert len(fl["pricing_tiers"]) >= 2

    def test_cost_estimate_has_tiers(self, initial_state):
        with patch_llm():
            result = build_architect_graph().invoke(initial_state)

        tiers = result["cost_estimate"].get("tiers", {})
        assert "startup" in tiers
        assert tiers["startup"]["monthly_usd"] > 0

    def test_approval_status_preserved(self, initial_state):
        with patch_llm():
            result = build_architect_graph().invoke(initial_state)

        assert result["approval_status"] == "approved"

    def test_tokens_accumulated(self, initial_state):
        with patch_llm():
            result = build_architect_graph().invoke(initial_state)

        # FakeLLM returns 500 tokens per call × 8 nodes
        assert result["llm_tokens_used"] >= 500

    def test_state_converts_to_typed_output(self, initial_state):
        """Verify _state_to_output produces a valid ArchitectOutput."""
        with patch_llm():
            result = build_architect_graph().invoke(initial_state)

        raw_fl = result.get("feature_list") or {}
        feature_list = FeatureList(
            features=raw_fl.get("features", []),
            integrations=raw_fl.get("integrations", []),
            pricing_tiers=raw_fl.get("pricing_tiers", []),
        )
        requirements = [Requirement(**r) for r in result.get("requirements", [])]

        output = ArchitectOutput(
            run_id=result["run_id"],
            organization_id=result["organization_id"],
            requirements=requirements,
            erd_mermaid=result.get("erd_mermaid", ""),
            openapi_3_1=result.get("openapi_3_1", {}),
            stack=result.get("stack", {}),
            microservice_boundaries=result.get("microservice_boundaries", []),
            auth_strategy=result.get("auth_strategy", {}),
            scaling_plan=result.get("scaling_plan", {}),
            cost_estimate=result.get("cost_estimate", {}),
            feature_list=feature_list,
            approval_status=result.get("approval_status", "pending"),
        )
        assert output.approval_status == "approved"
        assert len(output.feature_list.features) >= 8
