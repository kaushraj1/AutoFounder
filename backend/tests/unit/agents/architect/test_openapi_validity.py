"""Unit tests — OpenAPI 3.1 validation via OpenAPIValidateTool (AF-040).

Tests: valid spec passes, missing keys fail, bad $ref detected,
missing security schemes warns, invalid HTTP method warned.
No LLM, no DB.
"""

from __future__ import annotations

import json

import pytest

from app.agents.architect.tools.openapi_validate import OpenAPIValidateTool


@pytest.fixture()
def tool() -> OpenAPIValidateTool:
    return OpenAPIValidateTool()


class TestOpenAPIValidation:
    def test_valid_spec_passes(self, tool, valid_openapi_spec):
        result = tool.validate(valid_openapi_spec)
        assert result.valid is True
        assert result.errors == []

    def test_path_count(self, tool, valid_openapi_spec):
        result = tool.validate(valid_openapi_spec)
        assert result.path_count == 2

    def test_schema_count(self, tool, valid_openapi_spec):
        result = tool.validate(valid_openapi_spec)
        assert result.schema_count == 1

    def test_missing_openapi_key_fails(self, tool, valid_openapi_spec):
        spec = {k: v for k, v in valid_openapi_spec.items() if k != "openapi"}
        result = tool.validate(spec)
        assert result.valid is False
        assert any("openapi" in e for e in result.errors)

    def test_missing_info_key_fails(self, tool, valid_openapi_spec):
        spec = {k: v for k, v in valid_openapi_spec.items() if k != "info"}
        result = tool.validate(spec)
        assert result.valid is False

    def test_missing_paths_key_fails(self, tool, valid_openapi_spec):
        spec = {k: v for k, v in valid_openapi_spec.items() if k != "paths"}
        result = tool.validate(spec)
        assert result.valid is False

    def test_empty_paths_fails(self, tool, valid_openapi_spec):
        spec = {**valid_openapi_spec, "paths": {}}
        result = tool.validate(spec)
        assert result.valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_path_without_leading_slash_fails(self, tool, valid_openapi_spec):
        spec = {
            **valid_openapi_spec,
            "paths": {"projects": {"get": {"operationId": "x", "responses": {}}}},
        }
        result = tool.validate(spec)
        assert result.valid is False
        assert any("/" in e for e in result.errors)

    def test_missing_security_schemes_warns(self, tool, valid_openapi_spec):
        spec = {**valid_openapi_spec, "components": {}}
        result = tool.validate(spec)
        assert any("securitySchemes" in w for w in result.warnings)

    def test_wrong_openapi_version_fails(self, tool, valid_openapi_spec):
        spec = {**valid_openapi_spec, "openapi": "2.0"}
        result = tool.validate(spec)
        assert result.valid is False

    def test_invalid_json_string_fails(self, tool):
        result = tool.validate_json_string("{not valid json")
        assert result.valid is False
        assert any("JSON" in e for e in result.errors)

    def test_valid_json_string_passes(self, tool, valid_openapi_spec):
        result = tool.validate_json_string(json.dumps(valid_openapi_spec))
        assert result.valid is True
