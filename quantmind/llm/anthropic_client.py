"""QuantMind v2 — native Anthropic client (langchain-anthropic).

``effort`` (extended thinking) is model-gated: only sent for Opus/Sonnet models
(Haiku returns HTTP 400 on it). Forward-compatible via regex.
"""
import re
from typing import Any

from langchain_anthropic import ChatAnthropic

from quantmind.llm.base_client import BaseLLMClient, normalize_content
from quantmind.llm.validators import validate_model

# Extended-thinking 'effort' is valid only on Opus/Sonnet (not Haiku).
_EFFORT_MODELS = re.compile(r"^claude-(opus|sonnet)-\d+")

_PASSTHROUGH_KWARGS = (
    "timeout",
    "max_retries",
    "api_key",
    "max_tokens",
    "temperature",
    "callbacks",
)


class NormalizedChatAnthropic(ChatAnthropic):
    def invoke(self, input, config=None, **kwargs):
        return normalize_content(super().invoke(input, config, **kwargs))

    async def ainvoke(self, input, config=None, **kwargs):
        return normalize_content(await super().ainvoke(input, config, **kwargs))


class AnthropicClient(BaseLLMClient):
    def get_provider_name(self) -> str:
        return "anthropic"

    def validate_model(self) -> bool:
        return validate_model("anthropic", self.model)

    def get_llm(self) -> Any:
        self.warn_if_unknown_model()
        llm_kwargs: dict[str, Any] = {"model": self.model}
        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        # 'effort' is model-gated.
        effort = self.kwargs.get("effort")
        if effort and _EFFORT_MODELS.match(str(self.model)):
            llm_kwargs["effort"] = effort

        for key in _PASSTHROUGH_KWARGS:
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]
        return NormalizedChatAnthropic(**llm_kwargs)
