"""Unit tests — llm_parse.py JSON parse-with-correction (AF-044)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.agents.marketing.utils.llm_parse import parse_with_correction


class TestParseWithCorrection:
    @pytest.mark.asyncio
    async def test_valid_json_returns_parsed_dict(self) -> None:
        """Valid JSON is parsed directly without calling the LLM."""
        raw = '{"brand_voice": "technical", "seo_keywords": ["saas"]}'
        result = await parse_with_correction(raw, "some prompt")
        assert result["brand_voice"] == "technical"
        assert result["seo_keywords"] == ["saas"]

    @pytest.mark.asyncio
    async def test_markdown_fences_stripped(self) -> None:
        """JSON wrapped in ```json ... ``` fences is stripped and parsed."""
        raw = '```json\n{"key": "value"}\n```'
        result = await parse_with_correction(raw, "some prompt")
        assert result["key"] == "value"

    @pytest.mark.asyncio
    async def test_markdown_fences_without_language_tag_stripped(self) -> None:
        """JSON wrapped in ``` ... ``` (no language tag) is parsed."""
        raw = '```\n{"x": 42}\n```'
        result = await parse_with_correction(raw, "some prompt")
        assert result["x"] == 42

    @pytest.mark.asyncio
    async def test_invalid_json_triggers_correction(self) -> None:
        """Invalid JSON → correction LLM call → parses corrected JSON."""
        raw = '{"key": "unclosed string'
        corrected = {"key": "corrected value"}

        with patch("app.agents.marketing.llm.call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = (corrected, 50)
            result = await parse_with_correction(raw, "original prompt")

        assert result["key"] == "corrected value"
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_json_no_correction_raises(self) -> None:
        """With max_correction_attempts=0, invalid JSON raises ValueError directly."""
        raw = "not json at all {"
        with pytest.raises(ValueError, match="LLM JSON parse failed"):
            await parse_with_correction(raw, "original prompt", max_correction_attempts=0)

    @pytest.mark.asyncio
    async def test_correction_llm_failure_raises_value_error(self) -> None:
        """If the correction LLM call also fails, raises ValueError."""
        raw = "{bad json}"

        with patch("app.agents.marketing.llm.call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = RuntimeError("LLM timeout")
            with pytest.raises(ValueError, match="correction also failed"):
                await parse_with_correction(raw, "original prompt", max_correction_attempts=1)

    @pytest.mark.asyncio
    async def test_whitespace_trimmed_before_parse(self) -> None:
        """Leading/trailing whitespace does not break parsing."""
        raw = '   \n  {"answer": true}  \n  '
        result = await parse_with_correction(raw, "prompt")
        assert result["answer"] is True

    @pytest.mark.asyncio
    async def test_empty_json_object_parsed(self) -> None:
        """Empty JSON object {} is valid and returned as empty dict."""
        raw = "{}"
        result = await parse_with_correction(raw, "prompt")
        assert result == {}
