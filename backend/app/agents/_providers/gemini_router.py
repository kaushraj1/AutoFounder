"""Euri-backed LLM router (OpenAI-compatible client).

All agent LLM calls go through the Euri API at
https://api.euron.one/api/v1/euri using the ``openai`` Python client.
This lets every agent (Pillars 1–7) call Gemini models — and any other
model Euri supports — without touching Google's SDK directly.

Usage (injected via DI into every BaseAgent subclass)::

    from app.agents._providers.gemini_router import GeminiRouter
    router = GeminiRouter()
    text = await router.complete(task_class="strategy_analysis", prompt="...")
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base import LLMRouterProtocol

logger = logging.getLogger("app.agents.providers.gemini_router")

#: Per-agent default models via Euri
_TASK_MODEL_MAP: dict[str, str] = {
    "strategy": "gemini-2.5-flash",
    "research": "gemini-2.5-flash",
    "product_planner": "gemini-2.5-flash",
    "architect": "gemini-2.5-flash",
    "coder": "gemini-2.5-pro",
    "reviewer": "gemini-2.5-flash",
    "devops": "gemini-2.5-flash",
    "marketing": "gemini-2.5-flash",
    "llmops": "gemini-2.5-flash",
}
_DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiRouter(LLMRouterProtocol):
    """Euri API router implementing LLMRouterProtocol.

    Uses ``openai.AsyncOpenAI`` pointed at the Euri base URL so agents
    can call any Gemini (or other) model through a single interface.

    Args:
        api_key: Euri API key. If empty, read from ``EURI_API_KEY`` env var
            via ``get_settings()`` at call time.
        default_model: Fallback model when task_class doesn't match any prefix.
    """

    def __init__(
        self,
        api_key: str = "",
        default_model: str = _DEFAULT_MODEL,
    ) -> None:
        self._api_key = api_key
        self._default_model = default_model

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        """Complete a prompt via Euri API and return the response text.

        Args:
            task_class: Agent task identifier, e.g. ``"strategy_analysis"``,
                ``"coder_generation"``. Used to resolve the target model.
            prompt: Fully-rendered prompt string.
            **kw: Optional flags:
                - ``json_mode=True`` → request JSON output from the model
                - ``response_format="json"`` → same as json_mode
                - ``system`` → system message string
                - ``temperature`` → float, default 0.7
                - ``model`` → override resolved model for this single call

        Returns:
            Completion text from the model.

        Raises:
            ValueError: If no Euri API key is available.
            openai.APIError: On API errors.
        """
        from openai import AsyncOpenAI

        from app.core.config import get_settings

        settings = get_settings()
        api_key = self._api_key or settings.euri_api_key
        if not api_key:
            raise ValueError(
                "Euri API key is not configured. "
                "Set EURI_API_KEY in backend/.env"
            )

        # Resolve model
        model = kw.pop("model", None) or self._resolve_model(task_class)

        # Build messages
        messages: list[dict[str, str]] = []
        system_msg: str | None = kw.pop("system", None)
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": prompt})

        # JSON mode
        json_mode = kw.pop("json_mode", False)
        response_format_val = kw.pop("response_format", None)
        use_json = json_mode or response_format_val == "json"

        temperature: float = kw.pop("temperature", 0.7)

        create_kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if use_json:
            create_kwargs["response_format"] = {"type": "json_object"}

        logger.info(
            "GeminiRouter → Euri: task_class=%s model=%s json=%s",
            task_class,
            model,
            use_json,
        )

        client = AsyncOpenAI(api_key=api_key, base_url=settings.euri_base_url)
        response = await client.chat.completions.create(**create_kwargs)
        return response.choices[0].message.content or ""

    def _resolve_model(self, task_class: str) -> str:
        """Longest-prefix match against ``_TASK_MODEL_MAP``."""
        normalised = task_class.lower().replace("-", "_")
        best: str | None = None
        for prefix in _TASK_MODEL_MAP:
            if normalised.startswith(prefix):
                if best is None or len(prefix) > len(best):
                    best = prefix
        return _TASK_MODEL_MAP[best] if best else self._default_model
