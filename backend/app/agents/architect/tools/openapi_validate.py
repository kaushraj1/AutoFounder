"""OpenAPI 3.1 validation tool (AF-040).

Validates a generated OpenAPI spec using openapi-spec-validator (local, free).
Falls back to structural checks if the library is not installed.

Install (optional but recommended):
    uv add openapi-spec-validator
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OpenAPIValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    path_count: int = 0
    schema_count: int = 0
    validator_used: str = "structural"  # "openapi-spec-validator" | "structural"


class OpenAPIValidateTool:
    """Validates an OpenAPI 3.1 dict against the spec.

    Uses openapi-spec-validator when available; falls back to structural
    checks otherwise. Both paths return the same result shape.

    Usage (standalone):
        tool = OpenAPIValidateTool()
        spec = {"openapi": "3.1.0", ...}
        result = tool.validate(spec)
        if not result.valid:
            print(result.errors)
    """

    # Minimum required top-level keys in a valid OpenAPI 3.1 object.
    REQUIRED_KEYS = {"openapi", "info", "paths"}

    def validate(self, spec: dict[str, Any]) -> OpenAPIValidationResult:
        """Validate an OpenAPI spec dict. Returns a structured result."""
        try:
            from openapi_spec_validator import validate as _validate
            from openapi_spec_validator.readers import read_from_filename  # noqa: F401

            errors: list[str] = []
            try:
                _validate(spec)
            except Exception as exc:
                errors.append(str(exc))

            return OpenAPIValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                path_count=len(spec.get("paths", {})),
                schema_count=len(spec.get("components", {}).get("schemas", {})),
                validator_used="openapi-spec-validator",
            )

        except ImportError:
            return self._structural_validate(spec)

    def validate_json_string(self, spec_json: str) -> OpenAPIValidationResult:
        """Parse a JSON string then validate it."""
        try:
            spec = json.loads(spec_json)
        except json.JSONDecodeError as exc:
            return OpenAPIValidationResult(
                valid=False,
                errors=[f"Invalid JSON: {exc}"],
                validator_used="structural",
            )
        return self.validate(spec)

    # ------------------------------------------------------------------
    # Structural fallback (no external library)
    # ------------------------------------------------------------------

    def _structural_validate(self, spec: dict[str, Any]) -> OpenAPIValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        # Top-level required keys
        for key in self.REQUIRED_KEYS:
            if key not in spec:
                errors.append(f"Missing required top-level key: '{key}'")

        # Version check
        openapi_version = spec.get("openapi", "")
        if not str(openapi_version).startswith("3."):
            errors.append(f"Expected OpenAPI 3.x, got '{openapi_version}'")

        # info block
        info = spec.get("info", {})
        for field_ in ("title", "version"):
            if not info.get(field_):
                errors.append(f"info.{field_} is missing or empty")

        # paths block
        paths = spec.get("paths", {})
        if not paths:
            errors.append("paths is empty — no endpoints defined")
        else:
            for path, methods in paths.items():
                if not path.startswith("/"):
                    errors.append(f"Path '{path}' must start with '/'")
                if not isinstance(methods, dict):
                    errors.append(f"Path '{path}' must be an object of HTTP methods")
                    continue
                for method in methods:
                    if method.lower() not in {
                        "get",
                        "post",
                        "put",
                        "patch",
                        "delete",
                        "head",
                        "options",
                    }:
                        warnings.append(f"Unexpected HTTP method '{method}' on '{path}'")

        # Security scheme check
        components = spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        if not security_schemes:
            warnings.append("No securitySchemes defined — all endpoints will be public")

        # $ref integrity (shallow check — not a full graph traversal)
        spec_str = json.dumps(spec)
        if '"$ref"' in spec_str:
            import re

            refs = re.findall(r'"#/([^"]+)"', spec_str)
            for ref in refs:
                parts = ref.split("/")
                node: Any = spec
                for part in parts:
                    if isinstance(node, dict) and part in node:
                        node = node[part]
                    else:
                        errors.append(f"Unresolved $ref: '#/{ref}'")
                        break

        return OpenAPIValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            path_count=len(paths),
            schema_count=len(components.get("schemas", {})),
            validator_used="structural",
        )
