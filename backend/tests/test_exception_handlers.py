"""Tests for global exception handlers and the RequestIdMiddleware.

Uses a minimal FastAPI app (not create_app) to isolate handler behaviour from
application-specific routes and services.  raise_server_exceptions=False lets
the ServerErrorMiddleware return our 500 envelope rather than re-raising.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnavailableError,
    UnprocessableError,
    register_exception_handlers,
)
from app.core.middleware import RequestIdMiddleware


# ---------------------------------------------------------------------------
# Minimal test app
# ---------------------------------------------------------------------------


class _Body(BaseModel):
    name: str
    value: int


def _make_error_app() -> FastAPI:
    app = FastAPI()
    # Middleware: CORSMiddleware omitted; RequestIdMiddleware is what we test.
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    @app.get("/not-found")
    async def raise_not_found() -> None:
        raise NotFoundError("item-99 not found", details={"id": "item-99"})

    @app.get("/conflict")
    async def raise_conflict() -> None:
        raise ConflictError("gate already decided")

    @app.get("/unprocessable")
    async def raise_unprocessable() -> None:
        raise UnprocessableError("business rule violated")

    @app.get("/forbidden")
    async def raise_forbidden() -> None:
        raise ForbiddenError("insufficient scope")

    @app.get("/unavailable")
    async def raise_unavailable() -> None:
        raise UnavailableError("LLM provider temporarily down")

    @app.get("/crash")
    async def raise_crash() -> None:
        raise RuntimeError("kaboom — internal details must not leak")

    @app.post("/validate-body")
    async def needs_body(payload: _Body) -> dict:
        return payload.model_dump()

    return app


@pytest.fixture(scope="module")
def error_client() -> TestClient:
    return TestClient(_make_error_app(), raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_envelope(body: dict) -> None:
    """Every error response must match the spec envelope shape."""
    assert "error" in body, "missing 'error' key"
    assert "meta" in body, "missing 'meta' key"
    err = body["error"]
    assert "code" in err
    assert "message" in err
    assert err["code"].startswith("AF_ERR_"), f"code not namespaced: {err['code']}"
    meta = body["meta"]
    assert "request_id" in meta
    assert "timestamp" in meta


# ---------------------------------------------------------------------------
# NotFoundError (AppError subclass → 404)
# ---------------------------------------------------------------------------


class TestNotFoundError:
    def test_status(self, error_client: TestClient) -> None:
        assert error_client.get("/not-found").status_code == 404

    def test_code(self, error_client: TestClient) -> None:
        assert error_client.get("/not-found").json()["error"]["code"] == "AF_ERR_NOT_FOUND"

    def test_message_from_exception(self, error_client: TestClient) -> None:
        assert "item-99" in error_client.get("/not-found").json()["error"]["message"]

    def test_details(self, error_client: TestClient) -> None:
        body = error_client.get("/not-found").json()
        assert body["error"]["details"]["id"] == "item-99"

    def test_envelope_shape(self, error_client: TestClient) -> None:
        _assert_envelope(error_client.get("/not-found").json())


# ---------------------------------------------------------------------------
# ConflictError → 409
# ---------------------------------------------------------------------------


class TestConflictError:
    def test_status(self, error_client: TestClient) -> None:
        assert error_client.get("/conflict").status_code == 409

    def test_code(self, error_client: TestClient) -> None:
        assert error_client.get("/conflict").json()["error"]["code"] == "AF_ERR_CONFLICT"

    def test_envelope_shape(self, error_client: TestClient) -> None:
        _assert_envelope(error_client.get("/conflict").json())


# ---------------------------------------------------------------------------
# Other AppError subclasses
# ---------------------------------------------------------------------------


class TestOtherAppErrors:
    def test_unprocessable_422(self, error_client: TestClient) -> None:
        assert error_client.get("/unprocessable").status_code == 422

    def test_forbidden_403(self, error_client: TestClient) -> None:
        assert error_client.get("/forbidden").status_code == 403

    def test_unavailable_503(self, error_client: TestClient) -> None:
        assert error_client.get("/unavailable").status_code == 503


# ---------------------------------------------------------------------------
# Pydantic RequestValidationError → 422
# ---------------------------------------------------------------------------


class TestValidationError:
    def test_status(self, error_client: TestClient) -> None:
        resp = error_client.post("/validate-body", json={"name": "foo"})  # missing 'value'
        assert resp.status_code == 422

    def test_code(self, error_client: TestClient) -> None:
        resp = error_client.post("/validate-body", json={"name": "foo"})
        assert resp.json()["error"]["code"] == "AF_ERR_VALIDATION"

    def test_errors_in_details(self, error_client: TestClient) -> None:
        resp = error_client.post("/validate-body", json={"name": "foo"})
        body = resp.json()
        assert "errors" in body["error"].get("details", {})

    def test_envelope_shape(self, error_client: TestClient) -> None:
        resp = error_client.post("/validate-body", json={"name": "foo"})
        _assert_envelope(resp.json())


# ---------------------------------------------------------------------------
# Unhandled exception → 500 with no leak
# ---------------------------------------------------------------------------


class TestUnhandledException:
    def test_status(self, error_client: TestClient) -> None:
        assert error_client.get("/crash").status_code == 500

    def test_code(self, error_client: TestClient) -> None:
        assert error_client.get("/crash").json()["error"]["code"] == "AF_ERR_INTERNAL"

    def test_no_stack_trace_in_body(self, error_client: TestClient) -> None:
        text = error_client.get("/crash").text
        assert "Traceback" not in text
        assert "RuntimeError" not in text

    def test_internal_message_not_leaked(self, error_client: TestClient) -> None:
        text = error_client.get("/crash").text
        assert "kaboom" not in text

    def test_generic_client_message(self, error_client: TestClient) -> None:
        message = error_client.get("/crash").json()["error"]["message"]
        assert "unexpected" in message.lower()

    def test_envelope_shape(self, error_client: TestClient) -> None:
        _assert_envelope(error_client.get("/crash").json())


# ---------------------------------------------------------------------------
# X-Request-ID middleware
# ---------------------------------------------------------------------------


class TestRequestId:
    def test_response_has_header(self, error_client: TestClient) -> None:
        resp = error_client.get("/not-found")
        header_names = {h.lower() for h in resp.headers}
        assert "x-request-id" in header_names

    def test_inbound_id_echoed_in_header(self, error_client: TestClient) -> None:
        resp = error_client.get("/not-found", headers={"X-Request-ID": "trace-abc"})
        assert resp.headers.get("x-request-id") == "trace-abc"

    def test_inbound_id_in_response_body(self, error_client: TestClient) -> None:
        resp = error_client.get("/not-found", headers={"X-Request-ID": "trace-xyz"})
        assert resp.json()["meta"]["request_id"] == "trace-xyz"

    def test_auto_generated_id_format(self, error_client: TestClient) -> None:
        resp = error_client.get("/crash")
        rid = resp.headers.get("x-request-id", "")
        assert rid.startswith("af-req-")

    def test_id_present_on_crash(self, error_client: TestClient) -> None:
        resp = error_client.get("/crash", headers={"X-Request-ID": "trace-crash"})
        assert resp.json()["meta"]["request_id"] == "trace-crash"
