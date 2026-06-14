"""AF-048: Versioned Prompt Registry.

Extends the JinjaPromptRegistry pattern with:
- Version tracking (semver strings stored alongside templates)
- Canary split (deterministic tenant-level A/B routing via SHA-256 hash)
- Variable validation (Jinja2 meta.find_undeclared_variables check)
- In-memory cache with TTL

Usage::

    registry = VersionedPromptRegistry("/path/to/templates")
    registry.register("product_planner/generate_prd", "product_planner/prompts/generate_prd.j2")
    rendered = registry.render(
        "product_planner/generate_prd",
        {"idea_normalised": "My SaaS", "domain": "B2B"},
        tenant_id="org-abc",
    )
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, meta
from pydantic import BaseModel


class PromptVersion(BaseModel):
    """Metadata for a single registered prompt version."""

    name: str
    version: str = "1.0.0"
    template_path: str
    variables: list[str] = []  # required template variables (populated on register)
    is_canary: bool = False


class VersionedPromptRegistry:
    """AF-048 Prompt Registry with versioning, canary splits, and variable validation.

    Prompts are stored on disk as Jinja2 ``.j2`` templates. Each registration
    binds a logical ``name`` to a file path and semantic version string. A canary
    variant can be registered alongside the active variant; tenants are routed to
    the canary deterministically based on a SHA-256 hash of their ``tenant_id``.

    In-memory caching avoids redundant disk reads; entries expire after ``ttl``
    seconds (default 300 s / 5 min).

    Args:
        templates_dir: Root directory that Jinja2's FileSystemLoader will search.
        canary_fraction: Fraction of tenants (0.0–1.0) to route to canary versions.
        ttl: Cache time-to-live in seconds for rendered and raw template content.
    """

    def __init__(
        self,
        templates_dir: str | Path,
        *,
        canary_fraction: float = 0.1,
        ttl: float = 300.0,
    ) -> None:
        self._templates_dir = Path(templates_dir)
        self._canary_fraction = canary_fraction
        self._ttl = ttl

        self._jinja_env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=False,
            keep_trailing_newline=True,
        )

        # name → list of PromptVersion, sorted active-first, canary-last
        self._versions: dict[str, list[PromptVersion]] = {}
        # cache key → (content, expiry_monotonic)
        self._cache: dict[str, tuple[str, float]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        template_path: str,
        *,
        version: str = "1.0.0",
        is_canary: bool = False,
    ) -> None:
        """Register a prompt version programmatically.

        Calling this twice with the same ``name`` and ``version`` overwrites
        the existing registration. Canary and active versions coexist under the
        same ``name``.

        Args:
            name: Logical prompt key (e.g. ``"product_planner/generate_prd"``).
            template_path: Path to the ``.j2`` template file, relative to
                ``templates_dir``.
            version: Semver string (e.g. ``"1.2.0"``).
            is_canary: When ``True`` this registration is the canary variant.
        """
        variables = self._extract_variables(template_path)
        pv = PromptVersion(
            name=name,
            version=version,
            template_path=template_path,
            variables=variables,
            is_canary=is_canary,
        )
        bucket = self._versions.setdefault(name, [])
        # Replace any existing entry with same version + canary flag
        self._versions[name] = [
            v for v in bucket if not (v.version == version and v.is_canary == is_canary)
        ]
        self._versions[name].append(pv)

    def get(
        self,
        key: str,
        version: str | None = None,
        *,
        tenant_id: str | None = None,
    ) -> str:
        """Get prompt template source string.

        If a canary version is registered for ``key`` and ``tenant_id`` hashes
        into the canary fraction, return the canary template. Otherwise return
        the active (non-canary) template.

        Raises:
            KeyError: If ``key`` is not registered.
            FileNotFoundError: If the resolved template file does not exist.
        """
        cache_key = f"{key}::{version}::{tenant_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        pv = self._resolve_version(key, version=version, tenant_id=tenant_id)
        source = self._load_source(pv.template_path)
        self._set_cache(cache_key, source)
        return source

    def render(
        self,
        key: str,
        context: dict[str, Any],
        *,
        version: str | None = None,
        tenant_id: str | None = None,
    ) -> str:
        """Get and render a template with ``context``.

        Validates that all required variables declared in the template are
        present in ``context`` before rendering.

        Args:
            key: Logical prompt key.
            context: Template variables to render with.
            version: Pin to a specific semver; ``None`` uses active/canary routing.
            tenant_id: Used for deterministic canary routing.

        Returns:
            Rendered string output.

        Raises:
            KeyError: If ``key`` is not registered.
            ValueError: If required variables are missing from ``context``.
        """
        missing = self.validate_variables(key, context)
        if missing:
            raise ValueError(
                f"Prompt '{key}' is missing required variables: {missing}"
            )

        source = self.get(key, version, tenant_id=tenant_id)
        template = self._jinja_env.from_string(source)
        return template.render(**context)

    def validate_variables(self, key: str, context: dict[str, Any]) -> list[str]:
        """Return a list of required template variables missing from ``context``.

        Args:
            key: Logical prompt key (must be registered).
            context: Variable dict to check against.

        Returns:
            List of variable names missing from ``context``. Empty list means
            all required variables are present.
        """
        versions = self._versions.get(key)
        if not versions:
            raise KeyError(f"Prompt '{key}' is not registered")
        # Use the active version's variable list
        active = self._pick_active(versions)
        return [v for v in active.variables if v not in context]

    def list_registered(self) -> list[PromptVersion]:
        """Return all registered PromptVersion entries (active and canary)."""
        result: list[PromptVersion] = []
        for versions in self._versions.values():
            result.extend(versions)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_version(
        self,
        key: str,
        *,
        version: str | None,
        tenant_id: str | None,
    ) -> PromptVersion:
        """Select the correct PromptVersion for the request.

        Priority order:
        1. If ``version`` is pinned, find exact match (canary-agnostic).
        2. If canary version exists and tenant hashes into canary fraction, return canary.
        3. Return active (non-canary) version.
        """
        versions = self._versions.get(key)
        if not versions:
            raise KeyError(f"Prompt '{key}' is not registered")

        if version is not None:
            for pv in versions:
                if pv.version == version:
                    return pv
            raise KeyError(f"Prompt '{key}' version '{version}' not found")

        canary_versions = [pv for pv in versions if pv.is_canary]
        if canary_versions and tenant_id is not None:
            if self._tenant_in_canary(tenant_id):
                return canary_versions[-1]

        return self._pick_active(versions)

    def _pick_active(self, versions: list[PromptVersion]) -> PromptVersion:
        """Return the non-canary version, falling back to any version if none active."""
        active = [pv for pv in versions if not pv.is_canary]
        if active:
            return active[-1]
        return versions[-1]

    def _tenant_in_canary(self, tenant_id: str) -> bool:
        """Return True if ``tenant_id`` deterministically hashes into the canary bucket."""
        digest = hashlib.sha256(tenant_id.encode()).hexdigest()
        # Take the first 8 hex chars as a uint32 and normalise to [0, 1)
        bucket = int(digest[:8], 16) / 0xFFFFFFFF
        return bucket < self._canary_fraction

    def _load_source(self, template_path: str) -> str:
        """Load raw template source from disk via Jinja2's loader."""
        try:
            source, _, _ = self._jinja_env.loader.get_source(  # type: ignore[union-attr]
                self._jinja_env, template_path
            )
            return source
        except TemplateNotFound as exc:
            full_path = self._templates_dir / template_path
            raise FileNotFoundError(
                f"Template not found: {full_path}"
            ) from exc

    def _extract_variables(self, template_path: str) -> list[str]:
        """Parse the template and return a sorted list of undeclared variable names."""
        try:
            source = self._load_source(template_path)
            ast = self._jinja_env.parse(source)
            undeclared = meta.find_undeclared_variables(ast)
            return sorted(undeclared)
        except (FileNotFoundError, TemplateNotFound):
            # Template may not exist yet at register time (deferred load)
            return []

    def _get_cached(self, cache_key: str) -> str | None:
        """Return cached value if it exists and has not expired."""
        entry = self._cache.get(cache_key)
        if entry is None:
            return None
        content, expiry = entry
        if time.monotonic() > expiry:
            del self._cache[cache_key]
            return None
        return content

    def _set_cache(self, cache_key: str, content: str) -> None:
        """Store ``content`` in the in-memory cache with TTL."""
        self._cache[cache_key] = (content, time.monotonic() + self._ttl)
