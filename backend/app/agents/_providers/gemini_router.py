import logging
from typing import Any

import google.generativeai as genai

from app.agents.base import LLMRouterProtocol

logger = logging.getLogger("app.agents.providers.gemini_router")


class GeminiRouter(LLMRouterProtocol):
    """Router implementation using google-generativeai (Gemini SDK) with fallback to Euri API."""

    def __init__(self, api_key: str, default_model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key
        self.default_model = default_model
        from app.core.config import get_settings

        settings = get_settings()
        if api_key and not settings.euri_api_key:
            genai.configure(api_key=api_key)

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        """Complete prompt using Gemini or Euri Model."""
        import httpx
        from app.core.config import get_settings

        settings = get_settings()

        euri_key = settings.euri_api_key
        if euri_key:
            base_url = settings.euri_base_url
            endpoint = f"{base_url.rstrip('/')}/chat/completions"
            model_name = settings.euri_model

            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {euri_key}"}

            payload: dict[str, Any] = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
            }
            if kw.get("response_format") == "json" or kw.get("json_mode", False):
                payload["response_format"] = {"type": "json_object"}

            logger.info("Routing completion to Euri API (model=%s, url=%s)", model_name, endpoint)

            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, headers=headers, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        if not self.api_key:
            logger.error("Gemini API key is missing from GeminiRouter config")
            raise ValueError("Gemini API key is not configured.")

        model_name = kw.get("model") or self.default_model

        # Extract json_mode configuration
        generation_config: dict[str, Any] = {}
        if kw.get("response_format") == "json" or kw.get("json_mode", False):
            generation_config["response_mime_type"] = "application/json"

        # Initialize and invoke the GenerativeModel
        model = genai.GenerativeModel(model_name)
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config if generation_config else None,  # type: ignore
        )
        return response.text
