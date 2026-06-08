import logging
from typing import Any

import google.generativeai as genai

from app.agents.base import LLMRouterProtocol

logger = logging.getLogger("app.agents.providers.gemini_router")


class GeminiRouter(LLMRouterProtocol):
    """Router implementation using google-generativeai (Gemini SDK)."""

    def __init__(self, api_key: str, default_model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key
        self.default_model = default_model
        if api_key:
            genai.configure(api_key=api_key)

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        """Complete prompt using Gemini Model."""
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
