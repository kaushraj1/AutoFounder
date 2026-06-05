"""Tenant-scoped object store client (Supabase Storage).

All paths are prefixed with "org_{org_id}/" so tenant assets are physically
separated in the bucket and a mis-configured search_path can never expose
another tenant's files.

The supabase client is imported lazily so the core backend boots without
the optional 'data' dependency group installed.  Production and agent
workers install it; `uv sync --group data`.

Usage:
    obj = udal.object()
    url = await obj.upload("artifacts/lean_canvas.json", data, "application/json")
    content = await obj.download("artifacts/lean_canvas.json")
"""

from __future__ import annotations

import importlib
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_BUCKET = "autofounder-artifacts"


def _supabase_client():
    """Lazy import — raises ImportError with a helpful message if not installed."""
    try:
        supabase_mod = importlib.import_module("supabase")
        settings = get_settings()
        return supabase_mod.create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
    except ImportError as exc:
        raise ImportError(
            "supabase package not installed.  "
            "Run: uv sync --group data"
        ) from exc


class ObjectClient:
    """Supabase Storage access scoped to a single tenant."""

    def __init__(self, org_id: str) -> None:
        self._org_id = org_id
        self._prefix = f"org_{org_id}"

    def _full_path(self, path: str) -> str:
        return f"{self._prefix}/{path.lstrip('/')}"

    async def upload(
        self, path: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        """Upload bytes and return the public URL."""
        full = self._full_path(path)
        client = _supabase_client()
        client.storage.from_(_BUCKET).upload(
            full,
            data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return self.public_url(path)

    async def download(self, path: str) -> bytes:
        """Download and return raw bytes."""
        full = self._full_path(path)
        client = _supabase_client()
        return client.storage.from_(_BUCKET).download(full)

    async def delete(self, path: str) -> None:
        full = self._full_path(path)
        client = _supabase_client()
        client.storage.from_(_BUCKET).remove([full])

    async def list_paths(self, prefix: str = "") -> list[str]:
        """Return all object paths under prefix (relative to the tenant root)."""
        full_prefix = self._full_path(prefix) if prefix else self._prefix
        client = _supabase_client()
        items = client.storage.from_(_BUCKET).list(full_prefix)
        return [item["name"] for item in (items or [])]

    def public_url(self, path: str) -> str:
        """Return the public URL for a stored object."""
        full = self._full_path(path)
        client = _supabase_client()
        res = client.storage.from_(_BUCKET).get_public_url(full)
        return str(res)
