"""Unit — heal patch test-file guard (D5: never patch tests)."""

from __future__ import annotations

import pytest

from app.agents.reviewer.nodes.auto_heal import is_test_file


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_app.py",
        "app/test_service.py",
        "service_test.py",
        "src/Button.test.ts",
        "src/Button.spec.ts",
        "frontend/__tests__/home.tsx",
        "backend/tests/unit/test_db.py",
    ],
)
def test_test_files_are_rejected(path: str) -> None:
    assert is_test_file(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "app/service.py",
        "src/components/Button.tsx",
        "backend/app/db.py",
        "index.ts",
    ],
)
def test_source_files_are_allowed(path: str) -> None:
    assert is_test_file(path) is False
