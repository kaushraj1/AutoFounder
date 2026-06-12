"""Integration test — FeatureList contract matches Pillar 3 + Pillar 6 shape (AF-040).

Verifies the FeatureList produced by the graph exactly matches the
contract that Kartik (P3) and Pallavi (P6) will consume.
"""

from __future__ import annotations

import pytest

from app.agents.architect.graph import build_architect_graph
from app.agents.architect.schema import FeatureList
from tests.integration.agents.architect.fake_llm import patch_llm


@pytest.fixture()
def base_state() -> dict:
    return {
        "run_id": "00000000-0000-0000-0000-000000000002",
        "organization_id": "org-test",
        "idea_normalised": "A secrets management SaaS",
        "viability_band": "high",
        "lean_canvas": {},
        "prd": "PRD for featurelist handoff test",
        "approval_status": "approved",
        "errors": [],
        "llm_tokens_used": 0,
    }


class TestFeatureListHandoff:
    def test_featurelist_shape_matches_pydantic_schema(self, base_state):
        """Raw feature_list dict from state must be valid FeatureList."""
        with patch_llm():
            result = build_architect_graph().invoke(base_state)

        raw = result.get("feature_list", {})
        # This call raises ValidationError if shape is wrong
        fl = FeatureList(
            features=raw.get("features", []),
            integrations=raw.get("integrations", []),
            pricing_tiers=raw.get("pricing_tiers", []),
        )
        assert fl.features  # non-empty (FATAL guard already tested)

    def test_featurelist_features_are_strings(self, base_state):
        with patch_llm():
            result = build_architect_graph().invoke(base_state)

        features = result["feature_list"]["features"]
        assert all(isinstance(f, str) for f in features)

    def test_featurelist_integrations_are_strings(self, base_state):
        with patch_llm():
            result = build_architect_graph().invoke(base_state)

        integrations = result["feature_list"].get("integrations", [])
        assert all(isinstance(i, str) for i in integrations)

    def test_featurelist_pricing_tiers_have_name_and_price(self, base_state):
        with patch_llm():
            result = build_architect_graph().invoke(base_state)

        tiers = result["feature_list"].get("pricing_tiers", [])
        for tier in tiers:
            assert "name" in tier, f"Tier missing 'name': {tier}"
            assert "price_usd_monthly" in tier, f"Tier missing 'price_usd_monthly': {tier}"

    def test_empty_featurelist_triggers_fatal_error(self, base_state):
        """If compose_featurelist returns empty features, errors list must contain FATAL."""
        def _fake_empty_featurelist(prompt, **_):
            return {"features": [], "integrations": [], "pricing_tiers": []}, 0

        from unittest.mock import patch as mock_patch
        # patch_llm() is outer (all nodes); inner override wins for compose_featurelist
        with patch_llm():
            with mock_patch(
                "app.agents.architect.nodes.compose_featurelist.call_llm",
                side_effect=_fake_empty_featurelist,
            ):
                result = build_architect_graph().invoke(base_state)

        # Graph should reach error_end — errors must mention FATAL
        assert any("FATAL" in e or "empty" in e.lower() for e in result.get("errors", []))
