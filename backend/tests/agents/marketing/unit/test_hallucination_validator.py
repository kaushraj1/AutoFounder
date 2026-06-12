"""Unit tests — hallucination cross-reference validator (AF-044, T5)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.marketing.nodes.hallucination_check import (
    hallucination_check,
    validate_claims_against_features,
)


class TestHallucinationCheckNode:
    """Tests for hallucination_check as a LangGraph node."""

    @pytest.mark.asyncio
    async def test_passes_when_no_criticals(self) -> None:
        """Hallucination check passes when critical_count == 0."""
        state = _base_state()

        mock_response = json.dumps(
            {
                "critical_count": 0,
                "warning_count": 1,
                "passed": True,
                "findings": [
                    {
                        "claim": "Fast setup",
                        "severity": "WARNING",
                        "reason": "implied",
                        "corrected_claim": "",
                    }
                ],
            }
        )

        with patch(
            "app.agents.marketing.nodes.hallucination_check.call_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = (json.loads(mock_response), 500)
            result = await hallucination_check(state)

        assert result["hallucination_passed"] is True
        assert result["hallucination_report"]["critical_count"] == 0

    @pytest.mark.asyncio
    async def test_fails_when_criticals_present(self) -> None:
        """T5 setup: Hallucination fails when critical_count > 0."""
        state = _base_state()

        mock_response = json.dumps(
            {
                "critical_count": 2,
                "warning_count": 1,
                "passed": False,
                "findings": [
                    {
                        "claim": "Supports unlimited projects",
                        "source_node": "landing_page",
                        "severity": "CRITICAL",
                        "reason": "Not in feature list",
                        "corrected_claim": "",
                    }
                ],
            }
        )

        with patch(
            "app.agents.marketing.nodes.hallucination_check.call_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = (json.loads(mock_response), 500)
            result = await hallucination_check(state)

        assert result["hallucination_passed"] is False
        assert result["hallucination_report"]["critical_count"] == 2

    @pytest.mark.asyncio
    async def test_llm_failure_passes_with_warning(self) -> None:
        """On LLM failure, hallucination check passes with WARNING (non-fatal)."""
        state = _base_state()

        with patch(
            "app.agents.marketing.nodes.hallucination_check.call_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.side_effect = RuntimeError("LLM timeout")
            result = await hallucination_check(state)

        assert result["hallucination_passed"] is True
        assert result["hallucination_report"]["warning_count"] >= 1
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_retry_count_tracked(self) -> None:
        """Retry count from state is preserved in hallucination_report."""
        state = _base_state()
        state["hallucination_retry_count"] = 1

        mock_response = json.dumps(
            {"critical_count": 0, "warning_count": 0, "passed": True, "findings": []}
        )

        with patch(
            "app.agents.marketing.nodes.hallucination_check.call_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = (json.loads(mock_response), 100)
            result = await hallucination_check(state)

        assert result["hallucination_report"]["retry_count"] == 1


class TestStandaloneHallucinationValidator:
    """Tests for the standalone validate_claims_against_features function."""

    @pytest.mark.asyncio
    async def test_empty_claims_returns_pass(self) -> None:
        result = await validate_claims_against_features([], {"features": ["Feature A"]})
        assert result["passed"] is True
        assert result["critical_count"] == 0

    @pytest.mark.asyncio
    async def test_hallucinated_claim_detected(self) -> None:
        """Injected hallucination should be detected."""
        claims = ["Supports unlimited storage"]
        feature_list = {"features": ["10GB storage per account"]}

        mock_response = json.dumps(
            {
                "critical_count": 1,
                "warning_count": 0,
                "passed": False,
                "findings": [
                    {
                        "claim": "Supports unlimited storage",
                        "severity": "CRITICAL",
                        "reason": "Feature list says 10GB limit",
                        "corrected_claim": "10GB storage per account",
                    }
                ],
            }
        )

        with patch(
            "app.agents.marketing.nodes.hallucination_check.call_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = (json.loads(mock_response), 300)
            result = await validate_claims_against_features(claims, feature_list)

        assert result["passed"] is False
        assert result["critical_count"] == 1

    @pytest.mark.asyncio
    async def test_accurate_claim_passes(self) -> None:
        claims = ["Encrypted secret vault"]
        feature_list = {"features": ["Encrypted secret vault", "RBAC", "CLI integration"]}

        mock_response = json.dumps(
            {"critical_count": 0, "warning_count": 0, "passed": True, "findings": []}
        )

        with patch(
            "app.agents.marketing.nodes.hallucination_check.call_llm", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = (json.loads(mock_response), 200)
            result = await validate_claims_against_features(claims, feature_list)

        assert result["passed"] is True


def _base_state() -> dict:
    return {
        "run_id": "test-001",
        "organization_id": "org-test",
        "feature_list": {
            "features": ["Auth", "Payments", "Email"],
            "integrations": ["Stripe"],
            "pricing_tiers": [{"name": "Free"}, {"name": "Pro", "price": "$12/mo"}],
        },
        "landing_page": {
            "hero_headline": "Ship fast",
            "features_section": [{"title": "Auth", "description": "Pre-configured auth"}],
            "faq_section": [],
        },
        "product_hunt_kit": {
            "tagline": "Ship your SaaS fast",
            "description": "A boilerplate with auth and billing.",
            "first_comment": "Hello PH!",
        },
        "social_post_bundle": {
            "x_thread": ["Launching today!", "It has auth and billing pre-wired."],
            "linkedin_post": "Excited to launch!",
        },
        "email_sequences": {
            "onboarding": [
                {
                    "subject": "Welcome!",
                    "preview_text": "Get started",
                    "body_html": "<p>Hi</p>",
                    "body_text": "Hi",
                }
            ],
            "reactivation": [],
        },
        "errors": [],
        "llm_tokens_used": 0,
        "hallucination_retry_count": 0,
    }
