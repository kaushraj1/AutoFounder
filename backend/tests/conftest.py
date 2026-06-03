"""Shared pytest fixtures."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import run_service


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient bound to a fresh app instance."""
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _reset_run_store() -> Iterator[None]:
    """Keep the in-memory run store isolated between tests."""
    run_service._reset_store()
    yield
    run_service._reset_store()
