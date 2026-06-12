"""Unit — credential redaction for repo URLs."""

from __future__ import annotations

import pytest

from app.agents.reviewer.utils.redact import redact_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://x-access-token:ghs_secret@github.com/org/repo.git",
            "https://github.com/org/repo.git",
        ),
        ("https://user:pass@gitlab.com/a/b", "https://gitlab.com/a/b"),
        ("https://github.com/org/repo", "https://github.com/org/repo"),  # nothing to strip
        ("git@github.com:org/repo.git", "git@github.com:org/repo.git"),  # ssh form untouched
        ("", ""),
        ("local", "local"),
    ],
)
def test_redact_url(url: str, expected: str) -> None:
    assert redact_url(url) == expected
