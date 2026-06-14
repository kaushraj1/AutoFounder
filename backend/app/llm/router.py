"""AF-049: Task-class to model routing.

Routes by ``task_class`` prefix to the appropriate model:

- ``"strategy_*"``       → gemini-2.0-flash
- ``"architect_*"``      → gemini-2.0-flash
- ``"coder_*"``          → gemini-2.0-flash  (larger context)
- ``"reviewer_*"``       → gemini-2.0-flash
- ``"devops_*"``         → gemini-2.0-flash
- ``"marketing_*"``      → gemini-2.0-flash
- ``"product_planner_*"``→ gemini-2.0-flash
- ``default``            → gemini-2.0-flash

Falls back to the Euri API (``EURI_API_KEY``) when the env var is set, in
line with how ``GeminiRouter`` already behaves.

Usage::

    router = LLMRouter()
    text = await router.complete(task_class="architect_design", prompt="...")
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("app.llm.router")

#: Mapping from task-class prefix → model name.
TASK_CLASS_MODEL_MAP: dict[str, str] = {
    "strategy": "gemini-2.0-flash",
    "architect": "gemini-2.0-flash",
    "coder": "gemini-2.0-flash",
    "reviewer": "gemini-2.0-flash",
    "devops": "gemini-2.0-flash",
    "marketing": "gemini-2.0-flash",
    "product_planner": "gemini-2.0-flash",
}

_DEFAULT_MODEL = "gemini-2.0-flash"


class LLMRouter:
    """AF-049 task-class based model router with Euri / Gemini backend.

    Selects the target model by matching ``task_class`` against
    ``TASK_CLASS_MODEL_MAP`` (longest-prefix wins). Delegates to either the
    Euri API (when ``EURI_API_KEY`` is configured) or the Google Gemini SDK.

    Args:
        default_model: Fallback model when no prefix matches.
    """

    def __init__(self, default_model: str = _DEFAULT_MODEL) -> None:
        self._default_model = default_model

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        """Route to the correct model and return the completion text.

        Args:
            task_class: Dot-or-underscore-separated identifier (e.g.
                ``"architect_design"``). Matched against ``TASK_CLASS_MODEL_MAP``
                by longest prefix.
            prompt: The full rendered prompt string.
            **kw: Extra kwargs forwarded to the backend (e.g. ``json_mode=True``).

        Returns:
            Raw completion text from the model.

        Raises:
            ValueError: If no API key is configured.
            httpx.HTTPStatusError: On non-2xx responses from the Euri endpoint.
        """
        from app.core.config import get_settings

        model = self._resolve_model(task_class)
        settings = get_settings()

        if settings.euri_api_key:
            logger.debug(
                "LLMRouter: task_class=%s → euri model=%s", task_class, settings.euri_model
            )
            return await self._call_euri(settings.euri_model, prompt, settings=settings, **kw)

        logger.debug("LLMRouter: task_class=%s → gemini model=%s", task_class, model)
        return await self._call_gemini(model, prompt, settings=settings, **kw)

    def _resolve_model(self, task_class: str) -> str:
        """Find the best model for ``task_class`` using longest-prefix match.

        The task class may use either underscores or hyphens as separators.
        The map keys are prefix strings (e.g. ``"product_planner"``).
        """
        # Normalise separators
        normalised = task_class.lower().replace("-", "_")
        best: str | None = None
        for prefix, _model in TASK_CLASS_MODEL_MAP.items():
            if normalised.startswith(prefix):
                if best is None or len(prefix) > len(best):
                    best = prefix
        if best is not None:
            return TASK_CLASS_MODEL_MAP[best]  # type: ignore[index]
        return self._default_model

    async def _call_gemini(self, model: str, prompt: str, **kw: Any) -> str:
        """Call the Google Gemini SDK and return the response text.

        Args:
            model: Gemini model name (e.g. ``"gemini-2.0-flash"``).
            prompt: Rendered prompt string.
            **kw: Supports ``json_mode`` / ``response_format="json"`` to enable
                JSON MIME type on the generation config.

        Returns:
            Response text from the model.
        """
        import google.generativeai as genai

        settings = kw.pop("settings", None)
        api_key: str = ""
        if settings is not None:
            api_key = settings.gemini_api_key
        if not api_key:
            from app.core.config import get_settings as _gs

            api_key = _gs().gemini_api_key

        if not api_key:
            raise ValueError(
                "Gemini API key is not configured (set GEMINI_API_KEY or EURI_API_KEY)."
            )

        genai.configure(api_key=api_key)

        generation_config: dict[str, Any] = {}
        if kw.get("response_format") == "json" or kw.get("json_mode", False):
            generation_config["response_mime_type"] = "application/json"

        genai_model = genai.GenerativeModel(model)
        response = await genai_model.generate_content_async(
            prompt,
            generation_config=generation_config if generation_config else None,  # type: ignore[arg-type]
        )
        return response.text

    async def _call_euri(self, model: str, prompt: str, **kw: Any) -> str:
        """Call the Euri API (OpenAI-compatible) and return the completion text.

        Args:
            model: Model name as expected by the Euri endpoint.
            prompt: Rendered prompt string.
            **kw: Supports ``json_mode`` / ``response_format="json"`` and
                ``settings`` (Settings object).

        Returns:
            Completion text from the Euri API.
        """
        import httpx

        settings = kw.pop("settings", None)
        if settings is None:
            from app.core.config import get_settings as _gs

            settings = _gs()

        base_url: str = settings.euri_base_url
        euri_key: str = settings.euri_api_key
        endpoint = f"{base_url.rstrip('/')}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {euri_key}",
        }
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if kw.get("response_format") == "json" or kw.get("json_mode", False):
            payload["response_format"] = {"type": "json_object"}

        logger.debug("LLMRouter/_call_euri: model=%s endpoint=%s", model, endpoint)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint, headers=headers, json=payload, timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]  # type: ignore[index]
