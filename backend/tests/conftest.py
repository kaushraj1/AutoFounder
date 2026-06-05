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
def _reset_settings() -> Iterator[None]:
    """Isolate application settings between tests."""
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_run_store() -> Iterator[None]:
    """Keep the in-memory run store isolated between tests."""
    run_service._reset_store()
    yield
    run_service._reset_store()


@pytest.fixture(autouse=True)
def _reset_tenant_context() -> Iterator[None]:
    """Isolate the ContextVar tenant scope between tests."""
    from app.db.context import _org_id_var
    token = _org_id_var.set(None)
    yield
    _org_id_var.reset(token)
