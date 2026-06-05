"""Tests for JWT verification, OPA checks, mTLS, and ContextVar scoping."""

import pytest
import jwt
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import Principal, verify_jwt, verify_mtls
from app.api.deps import get_principal
from app.core.errors import register_exception_handlers
from app.db.context import get_tenant_context


# ---------------------------------------------------------------------------
# Unit tests for verify_jwt
# ---------------------------------------------------------------------------

def test_verify_jwt_valid() -> None:
    settings = get_settings()
    claims = {
        "sub": "user-123",
        "organization_id": "org-abc",
        "role": "founder",
        "scope": "runs:read runs:write"
    }
    token = jwt.encode(claims, settings.supabase_jwt_secret, algorithm="HS256")
    
    principal = verify_jwt(token)
    assert principal.organization_id == "org-abc"
    assert principal.role == "founder"
    assert principal.scopes == ["runs:read", "runs:write"]


def test_verify_jwt_nested_app_metadata() -> None:
    settings = get_settings()
    claims = {
        "sub": "user-123",
        "app_metadata": {
            "organization_id": "org-xyz",
            "role": "admin",
            "scopes": ["runs:read"]
        }
    }
    token = jwt.encode(claims, settings.supabase_jwt_secret, algorithm="HS256")
    
    principal = verify_jwt(token)
    assert principal.organization_id == "org-xyz"
    assert principal.role == "admin"
    assert principal.scopes == ["runs:read"]


def test_verify_jwt_sub_fallback() -> None:
    settings = get_settings()
    claims = {
        "sub": "user-uuid-111",
        "role": "founder"
    }
    token = jwt.encode(claims, settings.supabase_jwt_secret, algorithm="HS256")
    
    principal = verify_jwt(token)
    assert principal.organization_id == "user-uuid-111"


def test_verify_jwt_invalid_signature() -> None:
    claims = {"sub": "user-123", "organization_id": "org-abc"}
    token = jwt.encode(claims, "wrong-secret-key", algorithm="HS256")
    
    with pytest.raises(ValueError, match="Invalid token"):
        verify_jwt(token)


# ---------------------------------------------------------------------------
# Unit tests for verify_mtls
# ---------------------------------------------------------------------------

def test_verify_mtls_disabled() -> None:
    settings = get_settings()
    settings.mtls_enabled = False
    
    app = FastAPI()
    @app.get("/")
    def index(request: Request):
        return {"ok": verify_mtls(request)}
        
    client = TestClient(app)
    response = client.get("/")
    assert response.json() == {"ok": True}


def test_verify_mtls_enabled_success() -> None:
    settings = get_settings()
    settings.mtls_enabled = True
    settings.mtls_allowed_dns = "CN=orchestrator.internal"
    
    app = FastAPI()
    @app.get("/")
    def index(request: Request):
        return {"ok": verify_mtls(request)}
        
    client = TestClient(app)
    response = client.get("/", headers={
        "X-SSL-Client-Verify": "SUCCESS",
        "X-SSL-Client-DN": "CN=orchestrator.internal"
    })
    assert response.json() == {"ok": True}


def test_verify_mtls_enabled_failures() -> None:
    settings = get_settings()
    settings.mtls_enabled = True
    settings.mtls_allowed_dns = "CN=orchestrator.internal"
    
    app = FastAPI()
    @app.get("/")
    def index(request: Request):
        return {"ok": verify_mtls(request)}
        
    client = TestClient(app)
    
    # Mismatch DN
    response = client.get("/", headers={
        "X-SSL-Client-Verify": "SUCCESS",
        "X-SSL-Client-DN": "CN=untrusted.internal"
    })
    assert response.json() == {"ok": False}
    
    # Failed verification
    response = client.get("/", headers={
        "X-SSL-Client-Verify": "FAILED",
        "X-SSL-Client-DN": "CN=orchestrator.internal"
    })
    assert response.json() == {"ok": False}


# ---------------------------------------------------------------------------
# FastAPI Dependency Scoping & Envelope Checks
# ---------------------------------------------------------------------------

@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    
    @app.get("/test-protected")
    def protected(principal: Principal = Depends(get_principal)):
        return {
            "org_id": principal.organization_id,
            "role": principal.role,
            "ctx_org_id": get_tenant_context()
        }
        
    return app


def test_get_principal_dev_fallback(test_app: FastAPI) -> None:
    settings = get_settings()
    settings.app_env = "development"
    settings.mtls_enabled = False
    
    client = TestClient(test_app)
    response = client.get("/test-protected")
    assert response.status_code == 200
    data = response.json()
    assert data["org_id"] == "org_dev"
    assert data["ctx_org_id"] == "org_dev"
    assert get_tenant_context() is None


def test_get_principal_prod_missing_token(test_app: FastAPI) -> None:
    settings = get_settings()
    settings.app_env = "production"
    settings.mtls_enabled = False
    
    client = TestClient(test_app)
    response = client.get("/test-protected")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AF_ERR_UNAUTHORIZED"


def test_get_principal_valid_jwt(test_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    settings.app_env = "production"
    settings.mtls_enabled = False
    
    async def mock_opa(*args, **kwargs):
        return True, None
    monkeypatch.setattr("app.api.deps.check_opa_policy", mock_opa)
    
    claims = {
        "sub": "user-1122",
        "organization_id": "org-555",
        "role": "founder"
    }
    token = jwt.encode(claims, settings.supabase_jwt_secret, algorithm="HS256")
    
    client = TestClient(test_app)
    response = client.get("/test-protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["org_id"] == "org-555"
    assert data["ctx_org_id"] == "org-555"
    assert get_tenant_context() is None


def test_get_principal_opa_denied(test_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    settings.app_env = "production"
    settings.mtls_enabled = False
    
    async def mock_opa(*args, **kwargs):
        return False, "Tenant has hit limit"
    monkeypatch.setattr("app.api.deps.check_opa_policy", mock_opa)
    
    claims = {
        "sub": "user-1122",
        "organization_id": "org-555",
        "role": "founder"
    }
    token = jwt.encode(claims, settings.supabase_jwt_secret, algorithm="HS256")
    
    client = TestClient(test_app)
    response = client.get("/test-protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AF_ERR_FORBIDDEN"
    assert "Tenant has hit limit" in response.json()["error"]["message"]
