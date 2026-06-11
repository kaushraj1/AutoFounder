"""Unit tests — ERD completeness via MermaidTool (AF-040).

Tests: entity detection, required columns (id/created_at/updated_at),
relationship parsing, format validation.
No LLM, no DB.
"""

from __future__ import annotations

import pytest

from app.agents.architect.tools.mermaid import MermaidTool


@pytest.fixture()
def tool() -> MermaidTool:
    return MermaidTool()


class TestMermaidValidation:
    def test_valid_erd_passes(self, tool, valid_erd_mermaid):
        result = tool.validate(valid_erd_mermaid)
        assert result.valid is True
        assert result.errors == []

    def test_entity_count(self, tool, valid_erd_mermaid):
        result = tool.validate(valid_erd_mermaid)
        assert result.entity_count == 4
        assert set(result.entities) == {"USER", "PROJECT", "SECRET", "AUDIT_LOG"}

    def test_relationship_count(self, tool, valid_erd_mermaid):
        result = tool.validate(valid_erd_mermaid)
        assert result.relationship_count == 4

    def test_missing_id_column_fails(self, tool):
        erd = """erDiagram
    USER {
        string email
        datetime created_at
        datetime updated_at
    }"""
        result = tool.validate(erd)
        assert result.valid is False
        assert any("id" in e for e in result.errors)

    def test_missing_created_at_fails(self, tool):
        erd = """erDiagram
    USER {
        uuid id PK
        datetime updated_at
    }"""
        result = tool.validate(erd)
        assert result.valid is False
        assert any("created_at" in e for e in result.errors)

    def test_missing_updated_at_fails(self, tool):
        erd = """erDiagram
    USER {
        uuid id PK
        datetime created_at
    }"""
        result = tool.validate(erd)
        assert result.valid is False
        assert any("updated_at" in e for e in result.errors)

    def test_empty_erd_fails(self, tool):
        result = tool.validate("")
        assert result.valid is False
        assert "empty" in result.errors[0].lower()

    def test_missing_erdiagram_header_fails(self, tool):
        erd = """USER {
        uuid id PK
        datetime created_at
        datetime updated_at
    }"""
        result = tool.validate(erd)
        assert result.valid is False

    def test_no_entities_fails(self, tool):
        result = tool.validate("erDiagram\n    USER ||--o{ ORDER : places")
        assert result.valid is False
        assert any("No entities" in e for e in result.errors)

    def test_format_for_display_preserves_header(self, tool, valid_erd_mermaid):
        formatted = tool.format_for_display(valid_erd_mermaid)
        assert formatted.startswith("erDiagram")
