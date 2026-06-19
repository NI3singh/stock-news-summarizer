"""QuantMind v2 — native Google Gemini client (langchain-google-genai).

Maps QuantMind's unified options to Gemini params: ``api_key`` (or GEMINI_API_KEY
from env) -> ``google_api_key``; a unified ``thinking_level`` -> ``thinking_level``
on Gemini 3, or an integer ``thinking_budget`` on Gemini 2.5.
"""
import os
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from quantmind.llm.api_key_env import get_api_key_env
from quantmind.llm.base_client import BaseLLMClient, normalize_content
from quantmind.llm.validators import validate_model
from quantmind.utils import logger

_PASSTHROUGH_KWARGS = ("timeout", "max_retries", "temperature", "callbacks")


class NormalizedChatGoogle(ChatGoogleGenerativeAI):
    def invoke(self, input, config=None, **kwargs):
        return normalize_content(super().invoke(input, config, **kwargs))

    async def ainvoke(self, input, config=None, **kwargs):
        return normalize_content(await super().ainvoke(input, config, **kwargs))


class GoogleClient(BaseLLMClient):
    def get_provider_name(self) -> str:
        return "google"

    def validate_model(self) -> bool:
        return validate_model("google", self.model)

    def get_llm(self) -> Any:
        self.warn_if_unknown_model()
        llm_kwargs: dict[str, Any] = {"model": self.model}

        # Unified api_key -> google_api_key (falls back to GEMINI_API_KEY in env).
        api_key = self.kwargs.get("api_key") or os.environ.get(
            get_api_key_env("google") or ""
        )
        if api_key:
            llm_kwargs["google_api_key"] = api_key

        # Unified thinking_level -> per-family param.
        thinking = self.kwargs.get("thinking_level")
        if thinking is not None:
            if str(self.model).startswith("gemini-3"):
                llm_kwargs["thinking_level"] = thinking
            else:
                try:
                    llm_kwargs["thinking_budget"] = int(thinking)
                except (TypeError, ValueError):
                    logger.debug(
                        "Ignoring thinking_level={} for non-Gemini-3 model {} "
                        "(2.5 expects an integer thinking_budget)",
                        thinking,
                        self.model,
                    )

        for key in _PASSTHROUGH_KWARGS:
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]
        return NormalizedChatGoogle(**llm_kwargs)
