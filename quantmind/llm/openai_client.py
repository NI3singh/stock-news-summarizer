"""QuantMind v2 — OpenAI-compatible provider family (the heart of the design).

A frozen ``ProviderSpec`` declaratively describes one provider; the
``OPENAI_COMPATIBLE_PROVIDERS`` registry is the single source of truth for the
whole family (openai, openrouter, ollama, groq, deepseek, xai, openai_compatible).
Provider quirks live in ``ChatOpenAI`` subclasses, not in the client.

base_url precedence (copy exactly):
    explicit client base_url > base_url_env > spec.base_url > SDK default
"""
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from langchain_openai import ChatOpenAI

from quantmind.llm.api_key_env import get_api_key_env
from quantmind.llm.base_client import BaseLLMClient, normalize_content
from quantmind.llm.capabilities import get_capabilities
from quantmind.llm.validators import validate_model


class NormalizedChatOpenAI(ChatOpenAI):
    """ChatOpenAI that normalizes content and routes structured output via the
    capability table."""

    def invoke(self, input, config=None, **kwargs):
        return normalize_content(super().invoke(input, config, **kwargs))

    async def ainvoke(self, input, config=None, **kwargs):
        return normalize_content(await super().ainvoke(input, config, **kwargs))

    def with_structured_output(self, schema, *, method=None, **kwargs):
        caps = get_capabilities(self.model_name)
        if caps.preferred_structured_method == "none":
            raise NotImplementedError(
                f"Model '{self.model_name}' does not support structured output."
            )
        method = method or caps.preferred_structured_method
        if method == "function_calling" and not caps.supports_tool_choice:
            # Bind the schema as a tool, but don't send tool_choice (model rejects it).
            kwargs.setdefault("tool_choice", None)
        return super().with_structured_output(schema, method=method, **kwargs)


class DeepSeekChatOpenAI(NormalizedChatOpenAI):
    """DeepSeek wire-format quirks placeholder.

    Reached only because the registry row points ``chat_class`` here. Tool-choice
    suppression is already handled by the capability table in the base class;
    override LangChain's ``_get_request_payload`` / ``_create_chat_result`` here
    if the ``reasoning_content`` round-trip needs custom handling.
    """


@dataclass(frozen=True)
class ProviderSpec:
    chat_class: type = NormalizedChatOpenAI
    base_url: str | None = None
    base_url_env: str | None = None
    key_optional: bool = False
    placeholder_key: str = "EMPTY"
    require_base_url: bool = False
    use_responses_api: bool = False


OPENAI_COMPATIBLE_PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec(use_responses_api=True),
    "openrouter": ProviderSpec(base_url="https://openrouter.ai/api/v1"),
    "groq": ProviderSpec(base_url="https://api.groq.com/openai/v1"),
    "xai": ProviderSpec(base_url="https://api.x.ai/v1"),
    "deepseek": ProviderSpec(
        base_url="https://api.deepseek.com", chat_class=DeepSeekChatOpenAI
    ),
    "ollama": ProviderSpec(
        base_url="http://localhost:11434/v1",
        base_url_env="OLLAMA_BASE_URL",
        key_optional=True,
        placeholder_key="ollama",
    ),
    "openai_compatible": ProviderSpec(require_base_url=True, key_optional=True),
}


def is_openai_compatible(provider: str) -> bool:
    return provider.lower() in OPENAI_COMPATIBLE_PROVIDERS


def _is_native_openai_base_url(base_url: str | None) -> bool:
    """True if base_url is api.openai.com / *.openai.com (or unset = SDK default)."""
    if not base_url:
        return True
    if "://" not in base_url:
        base_url = "https://" + base_url
    host = urlparse(base_url).hostname or ""
    return host == "api.openai.com" or host.endswith(".openai.com")


_PASSTHROUGH_KWARGS = (
    "timeout",
    "max_retries",
    "reasoning_effort",
    "temperature",
    "api_key",
    "callbacks",
    "http_client",
    "http_async_client",
)


class OpenAIClient(BaseLLMClient):
    def __init__(self, model, base_url=None, provider="openai", **kwargs):
        super().__init__(model, base_url, **kwargs)
        self.provider = provider.lower()

    def get_provider_name(self) -> str:
        return self.provider

    def validate_model(self) -> bool:
        return validate_model(self.provider, self.model)

    def get_llm(self) -> Any:
        self.warn_if_unknown_model()
        spec = OPENAI_COMPATIBLE_PROVIDERS.get(self.provider)
        chat_cls = spec.chat_class if spec else NormalizedChatOpenAI
        llm_kwargs: dict[str, Any] = {"model": self.model}

        if spec:
            env_base_url = (
                os.environ.get(spec.base_url_env) if spec.base_url_env else None
            )
            base_url = self.base_url or env_base_url or spec.base_url
            if spec.require_base_url and not base_url:
                raise ValueError(
                    f"Provider '{self.provider}' requires a base_url "
                    f"(set backend_url or the provider's base-url env var)."
                )
            if base_url:
                llm_kwargs["base_url"] = base_url

            api_key_env = get_api_key_env(self.provider)
            api_key = os.environ.get(api_key_env) if api_key_env else None
            if api_key:
                llm_kwargs["api_key"] = api_key
            elif spec.key_optional:
                llm_kwargs["api_key"] = spec.placeholder_key  # keyless local servers
            elif api_key_env:
                raise ValueError(
                    f"API key for '{self.provider}' not set. Set {api_key_env} in your .env."
                )

            # Responses API exists only on native OpenAI — a custom base_url
            # speaks only Chat Completions.
            if spec.use_responses_api and _is_native_openai_base_url(base_url):
                llm_kwargs["use_responses_api"] = True
        elif self.base_url:
            llm_kwargs["base_url"] = self.base_url

        for key in _PASSTHROUGH_KWARGS:
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]
        return chat_cls(**llm_kwargs)
