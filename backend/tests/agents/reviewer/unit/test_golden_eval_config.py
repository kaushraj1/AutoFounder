"""Unit — structural validation of the Reviewer golden eval config.

The golden suite (``tests/golden/reviewer/promptfoo.yaml``) is normally run by
promptfoo against a live model, which needs an API key and network. This test
runs with neither: it loads the YAML and asserts the config is well-formed and
that every prompt/test cross-reference is intact, so drift or typos in the
golden suite fail fast in CI instead of silently at eval time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

CONFIG_PATH = Path(__file__).resolve().parents[3] / "golden" / "reviewer" / "promptfoo.yaml"


def _load() -> dict[str, Any]:
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "promptfoo config must parse to a mapping"
    return data


def test_config_file_exists() -> None:
    assert CONFIG_PATH.is_file(), f"missing golden config: {CONFIG_PATH}"


def test_has_required_top_level_keys() -> None:
    data = _load()
    for key in ("description", "providers", "prompts", "tests"):
        assert key in data, f"promptfoo config missing top-level key: {key}"


def test_providers_are_well_formed() -> None:
    providers = _load()["providers"]
    assert isinstance(providers, list) and providers, "providers must be a non-empty list"
    assert all("id" in p for p in providers), "every provider needs an id"


def test_prompts_have_id_and_body() -> None:
    prompts = _load()["prompts"]
    assert isinstance(prompts, list) and prompts, "prompts must be a non-empty list"
    for p in prompts:
        assert p.get("id"), "every prompt needs an id"
        assert p.get("raw"), f"prompt {p.get('id')!r} needs a raw body"


def test_every_test_references_a_defined_prompt() -> None:
    data = _load()
    prompt_ids = {p["id"] for p in data["prompts"]}
    tests = data["tests"]
    assert isinstance(tests, list) and tests, "tests must be a non-empty list"
    for t in tests:
        ref = t.get("prompt")
        assert ref in prompt_ids, f"test references unknown prompt id: {ref!r}"
        assert t.get("assert"), f"test {t.get('description')!r} has no assertions"


def test_all_three_reasoning_nodes_are_covered() -> None:
    """judge, triage, and auto_heal must each have at least one eval prompt."""
    prompt_ids = {p["id"] for p in _load()["prompts"]}
    assert any(pid.startswith("judge") for pid in prompt_ids), "no llm_judge eval prompt"
    assert any(pid.startswith("triage") for pid in prompt_ids), "no triage eval prompt"
    assert any(pid.startswith("heal") for pid in prompt_ids), "no auto_heal eval prompt"
