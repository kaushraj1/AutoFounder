"""Mermaid ERD tool (AF-040).

Validates and renders Mermaid erDiagram syntax. Runs fully offline —
no external service required. Rendering to PNG/SVG is optional and
only attempted when the `mermaid-py` package is present.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ERDValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    entity_count: int = 0
    entities: list[str] = field(default_factory=list)
    relationship_count: int = 0


class MermaidTool:
    """Validates Mermaid erDiagram syntax and extracts metadata.

    Usage (standalone, no platform needed):
        tool = MermaidTool()
        result = tool.validate(erd_mermaid_string)
        if result.valid:
            print(result.entities)
    """

    # Required columns every entity must have.
    REQUIRED_COLUMNS = {"id", "created_at", "updated_at"}

    def validate(self, erd_mermaid: str) -> ERDValidationResult:
        """Validate an erDiagram string and return a structured result."""
        errors: list[str] = []
        stripped = erd_mermaid.strip()

        if not stripped:
            return ERDValidationResult(valid=False, errors=["ERD string is empty"])

        if not stripped.startswith("erDiagram"):
            errors.append("ERD must start with 'erDiagram'")

        entities = self._extract_entities(stripped)
        relationships = self._extract_relationships(stripped)

        if not entities:
            errors.append("No entities found in ERD — check Mermaid syntax")

        for entity in entities:
            missing = self._check_required_columns(stripped, entity)
            if missing:
                errors.append(
                    f"Entity '{entity}' is missing required column(s): {', '.join(missing)}"
                )

        return ERDValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            entity_count=len(entities),
            entities=entities,
            relationship_count=len(relationships),
        )

    def format_for_display(self, erd_mermaid: str) -> str:
        """Return a clean, consistently indented erDiagram string."""
        lines = erd_mermaid.strip().splitlines()
        result: list[str] = []
        inside_entity = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped == "erDiagram":
                result.append(stripped)
            elif re.match(r"^\w+\s*\{", stripped):
                result.append(f"    {stripped}")
                inside_entity = True
            elif stripped == "}" and inside_entity:
                result.append("    }")
                inside_entity = False
            elif inside_entity:
                result.append(f"        {stripped}")
            else:
                result.append(f"    {stripped}")

        return "\n".join(result)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_entities(self, erd: str) -> list[str]:
        """Extract entity names from an erDiagram block."""
        return re.findall(r"^\s*(\w+)\s*\{", erd, re.MULTILINE)

    def _extract_relationships(self, erd: str) -> list[str]:
        """Extract relationship lines (e.g. USER ||--o{ ORDER : places)."""
        return re.findall(
            r"^\s*\w+\s+[\|\}\{o]{2,4}--[\|\}\{o]{2,4}\s+\w+\s*:\s*.+",
            erd,
            re.MULTILINE,
        )

    def _check_required_columns(self, erd: str, entity: str) -> list[str]:
        """Return required columns missing from an entity block."""
        # Find the entity block content between { }
        pattern = rf"{re.escape(entity)}\s*\{{([^}}]*)\}}"
        match = re.search(pattern, erd, re.DOTALL)
        if not match:
            return list(self.REQUIRED_COLUMNS)

        block = match.group(1).lower()
        return [col for col in self.REQUIRED_COLUMNS if col not in block]
