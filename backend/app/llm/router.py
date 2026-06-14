"""AF-049: Task-class to model routing via Euri API.

All LLM calls go through the Euri API (OpenAI-compatible) at
https://api.euron.one/api/v1/euri — this lets us call Gemini models
(and any other model Euri supports) with a single unified client.

Task-class → model routing:

- ``"strategy_*"``        → gemini-2.5-flash
- ``"architect_*"``       → gemini-2.5-flash
- ``"coder_*"``           → gemini-2.5-pro   (larger context for code gen)
- ``"reviewer_*"``        → gemini-2.5-flash
- ``"devops_*"``          → gemini-2.5-flash
- ``"marketing_*"``       → gemini-2.5-flash
- ``"product_planner_*"`` → gemini-2.5-flash
- ``"llmops_*"``          → gemini-2.5-flash
- ``default``             → gemini-2.5-flash

Usage::

    router = LLMRouter()
    text = await router.complete(task_class="coder_generation", prompt="...")
    json_text = await router.complete(task_class="architect_design", prompt="...", json_mode=True)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("app.llm.router")

#: Mapping from task-class prefix → Euri/Gemini model name.
TASK_CLASS_MODEL_MAP: dict[str, str] = {
    "strategy": "gemini-2.5-flash",
    "architect": "gemini-2.5-flash",
    "coder": "gemini-2.5-pro",        # larger context for full codebase generation
    "reviewer": "gemini-2.5-flash",
    "devops": "gemini-2.5-flash",
    "marketing": "gemini-2.5-flash",
    "product_planner": "gemini-2.5-flash",
    "llmops": "gemini-2.5-flash",
}

_DEFAULT_MODEL = "gemini-2.5-flash"
_EURI_BASE_URL = "https://api.euron.one/api/v1/euri"


class LLMRouter:
    """AF-049 task-class based model router using the Euri API (OpenAI-compatible).

    Uses the ``openai`` Python client pointed at Euri's base URL so we can
    call Gemini models (and others) with a single unified interface.

    Args:
        default_model: Fallback model when no task-class prefix matches.
    """

    def __init__(self, default_model: str = _DEFAULT_MODEL) -> None:
        self._default_model = default_model

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        """Route prompt to the correct model via Euri and return the response text.

        Args:
            task_class: Identifier like ``"coder_generation"`` or ``"architect_design"``.
                Matched against ``TASK_CLASS_MODEL_MAP`` by longest prefix.
            prompt: The fully-rendered prompt string.
            **kw: Optional flags:
                - ``json_mode=True`` or ``response_format="json"`` → request JSON output
                - ``model`` → override the resolved model for this call
                - ``temperature`` → sampling temperature (default 0.7)
                - ``system`` → optional system message string

        Returns:
            Raw completion text from the model.

        Raises:
            ValueError: If ``EURI_API_KEY`` is not configured.
            openai.APIError: On non-2xx responses from the Euri endpoint.
        """
        from app.core.config import get_settings

        settings = get_settings()

        if not settings.euri_api_key:
            raise ValueError(
                "EURI_API_KEY is not configured. "
                "Set it in backend/.env or as an environment variable."
            )

        # Allow per-call model override, else resolve from task_class
        model = kw.pop("model", None) or self._resolve_model(task_class)

        logger.debug("LLMRouter: task_class=%s → model=%s", task_class, model)

        return await self._call_euri(
            model=model,
            prompt=prompt,
            api_key=settings.euri_api_key,
            **kw,
        )

    def _resolve_model(self, task_class: str) -> str:
        """Find the best model for ``task_class`` using longest-prefix match."""
        normalised = task_class.lower().replace("-", "_")
        best: str | None = None
        for prefix in TASK_CLASS_MODEL_MAP:
            if normalised.startswith(prefix):
                if best is None or len(prefix) > len(best):
                    best = prefix
        return TASK_CLASS_MODEL_MAP[best] if best else self._default_model

    async def _call_euri(
        self,
        *,
        model: str,
        prompt: str,
        api_key: str,
        **kw: Any,
    ) -> str:
        """Call the Euri API using the OpenAI-compatible client.

        Args:
            model: Model name (e.g. ``"gemini-2.5-flash"``).
            prompt: User prompt text.
            api_key: Euri API key.
            **kw: Supports ``json_mode``, ``response_format``, ``temperature``,
                ``system`` (system message string).

        Returns:
            Completion text from the model.
        """
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=_EURI_BASE_URL,
        )

        # Build messages list
        messages: list[dict[str, str]] = []
        system_msg: str | None = kw.pop("system", None)
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": prompt})

        # Build extra kwargs
        temperature: float = kw.pop("temperature", 0.7)

        # JSON mode
        json_mode = kw.pop("json_mode", False)
        response_format_kw = kw.pop("response_format", None)
        use_json = json_mode or response_format_kw == "json"

        create_kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if use_json:
            create_kwargs["response_format"] = {"type": "json_object"}

        logger.debug(
            "LLMRouter/_call_euri: model=%s json_mode=%s msgs=%d",
            model,
            use_json,
            len(messages),
        )

        response = await client.chat.completions.create(**create_kwargs)
        return response.choices[0].message.content or ""
