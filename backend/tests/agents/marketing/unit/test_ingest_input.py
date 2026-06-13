"""Unit tests — ingest_input node (AF-044, T2, T3)."""

from __future__ import annotations

import pytest

from app.agents.marketing.nodes.ingest_input import ingest_input


@pytest.mark.asyncio
async def test_valid_input_passes() -> None:
    """T1 setup: All required fields present → validated=True."""
    state = _base_state()
    result = await ingest_input(state)
    assert result["validated"] is True
    assert result["fatal_error"] is None
    assert result["effective_live_url"] == "https://example.com"


@pytest.mark.asyncio
async def test_empty_feature_list_is_fatal() -> None:
    """T3: Empty feature_list → FATAL (refuses generation)."""
    state = _base_state()
    state["feature_list"] = {"features": [], "integrations": [], "pricing_tiers": []}
    result = await ingest_input(state)
    assert result["validated"] is False
    assert result["fatal_error"] is not None
    assert "FATAL" in result["fatal_error"]


@pytest.mark.asyncio
async def test_missing_live_url_uses_placeholder() -> None:
    """T2: Empty live_url → placeholder; not fatal."""
    state = _base_state()
    state["live_url"] = ""
    result = await ingest_input(state)
    assert result["validated"] is True
    assert result["effective_live_url"] == "[PENDING_DEPLOY]"
    assert any("PENDING_DEPLOY" in e for e in result.get("errors", []))


@pytest.mark.asyncio
async def test_missing_product_name_is_fatal() -> None:
    """Missing product_name is FATAL."""
    state = _base_state()
    state["brand_config"]["product_name"] = ""
    result = await ingest_input(state)
    assert result["validated"] is False
    assert result["fatal_error"] is not None


@pytest.mark.asyncio
async def test_missing_idea_normalised_is_warning() -> None:
    """Missing idea_normalised is a warning, not fatal."""
    state = _base_state()
    state["idea_normalised"] = ""
    result = await ingest_input(state)
    assert result["validated"] is True
    assert result["fatal_error"] is None
    assert len(result.get("errors", [])) > 0


def _base_state() -> dict:
    return {
        "run_id": "test-001",
        "organization_id": "org-test",
        "idea_normalised": "A test product",
        "brand_config": {"product_name": "TestApp", "tone": "professional"},
        "feature_list": {
            "features": ["Feature A", "Feature B"],
            "integrations": ["Stripe"],
            "pricing_tiers": [{"name": "Free"}],
        },
        "live_url": "https://example.com",
        "errors": [],
        "llm_tokens_used": 0,
    }
