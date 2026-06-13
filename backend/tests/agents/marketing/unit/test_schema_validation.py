"""Unit tests — schema validation for Marketing Agent (AF-044, T1–T3)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.agents.marketing.schema import (
    BrandConfig,
    FeatureList,
    MarketerInput,
    ProductHuntKit,
)


class TestFeatureListValidation:
    def test_feature_list_with_features_passes(self) -> None:
        fl = FeatureList(
            features=["Auth", "Payments", "Email"],
            integrations=["Stripe"],
            pricing_tiers=[{"name": "Free"}],
        )
        assert len(fl.features) == 3

    def test_empty_feature_list_raises(self) -> None:
        """T3: Empty feature_list must FATAL."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            FeatureList(features=[])

    def test_feature_list_without_integrations(self) -> None:
        fl = FeatureList(features=["Feature A"])
        assert fl.integrations == []
        assert fl.pricing_tiers == []


class TestMarketerInputValidation:
    def test_valid_input_with_all_fields(self) -> None:
        inp = MarketerInput(
            run_id=uuid4(),
            organization_id="org-test",
            idea_normalised="Test idea",
            brand_config=BrandConfig(product_name="TestApp"),
            feature_list=FeatureList(features=["Feature A", "Feature B"]),
            live_url="https://test.com",
        )
        assert inp.brand_config.product_name == "TestApp"
        assert len(inp.feature_list.features) == 2

    def test_input_with_empty_live_url(self) -> None:
        """T2: Empty live_url must be accepted (handled by ingest_input node)."""
        inp = MarketerInput(
            run_id=uuid4(),
            organization_id="org-test",
            idea_normalised="Test idea",
            brand_config=BrandConfig(product_name="TestApp"),
            feature_list=FeatureList(features=["Feature A"]),
            live_url="",
        )
        assert inp.live_url == ""

    def test_input_empty_feature_list_raises(self) -> None:
        """T3: MarketerInput with empty feature_list must raise ValidationError."""
        with pytest.raises(ValidationError):
            MarketerInput(
                run_id=uuid4(),
                organization_id="org-test",
                idea_normalised="Test idea",
                brand_config=BrandConfig(product_name="TestApp"),
                feature_list=FeatureList(features=[]),
            )


class TestProductHuntKitValidation:
    def test_tagline_within_limit_passes(self) -> None:
        kit = ProductHuntKit(
            tagline="Ship your SaaS fast",  # well within 60 chars
            description="A Next.js boilerplate with auth and billing." * 2,
            first_comment="Hello PH!",
            maker_note="Built this to ship faster.",
        )
        assert kit.tagline == "Ship your SaaS fast"

    def test_tagline_exceeding_60_chars_raises(self) -> None:
        with pytest.raises(ValidationError, match="≤60 chars"):
            ProductHuntKit(
                tagline="A" * 61,  # 61 chars — should fail
                description="Description",
                first_comment="Comment",
                maker_note="Note",
            )

    def test_description_exceeding_260_chars_raises(self) -> None:
        with pytest.raises(ValidationError, match="≤260 chars"):
            ProductHuntKit(
                tagline="Good tagline",
                description="D" * 261,  # 261 chars — should fail
                first_comment="Comment",
                maker_note="Note",
            )


class TestBrandConfigDefaults:
    def test_brand_config_defaults(self) -> None:
        bc = BrandConfig(product_name="MyApp")
        assert bc.tone == "professional"
        assert bc.tagline == ""
        assert bc.primary_color == ""
