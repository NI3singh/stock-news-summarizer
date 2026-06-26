"""StockStalker v2 — LLM client factory.

Dispatch by provider name: native APIs (Anthropic, Google) are matched first;
everything else falls through to the OpenAI-compatible registry. Provider SDKs are
imported lazily, so importing this module never pulls a heavy SDK unless that
provider is actually requested.
"""
from stockstalker.llm.base_client import BaseLLMClient


def create_llm_client(
    provider: str, model: str, base_url: str | None = None, **kwargs
) -> BaseLLMClient:
    """Return a ready-to-use provider client for ``provider``/``model``."""
    p = provider.lower()
    if p == "anthropic":
        from stockstalker.llm.anthropic_client import AnthropicClient

        return AnthropicClient(model, base_url, **kwargs)
    if p == "google":
        from stockstalker.llm.google_client import GoogleClient

        return GoogleClient(model, base_url, **kwargs)

    from stockstalker.llm.openai_client import OpenAIClient, is_openai_compatible

    if is_openai_compatible(p):
        return OpenAIClient(model, base_url, provider=p, **kwargs)
    raise ValueError(f"Unsupported LLM provider: {provider}")
