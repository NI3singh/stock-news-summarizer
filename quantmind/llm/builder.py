"""QuantMind v2 — config → LLM bridge (spec §4.11).

Translates ``Settings`` into provider-specific kwargs and builds the deep/quick
LLM pair through the factory, so consumers (pipeline, agents) never re-implement
the config→kwargs mapping or branch on provider themselves.

Not exported from ``quantmind.llm.__init__`` on purpose — importing it pulls
config (and thus requires a valid .env), whereas ``import quantmind.llm`` stays
lightweight. Import it explicitly: ``from quantmind.llm.builder import build_llms``.
"""
from typing import Any

from quantmind.config import settings as _settings
from quantmind.llm.factory import create_llm_client


def get_provider_kwargs(config: Any | None = None) -> dict[str, Any]:
    """Translate config keys into provider-specific LLM kwargs."""
    config = config or _settings
    kwargs: dict[str, Any] = {}
    provider = (config.llm_provider or "").lower()

    if provider == "google" and config.google_thinking_level:
        kwargs["thinking_level"] = config.google_thinking_level
    elif provider == "openai" and config.openai_reasoning_effort:
        kwargs["reasoning_effort"] = config.openai_reasoning_effort
    elif provider == "anthropic" and config.anthropic_effort:
        kwargs["effort"] = config.anthropic_effort

    if config.temperature is not None:
        kwargs["temperature"] = float(config.temperature)
    return kwargs


def build_llms(config: Any | None = None, callbacks: Any | None = None) -> tuple[Any, Any]:
    """Build ``(deep_llm, quick_llm)`` from config via the factory."""
    config = config or _settings
    llm_kwargs = get_provider_kwargs(config)
    if callbacks:
        llm_kwargs["callbacks"] = callbacks

    provider = config.llm_provider
    backend_url = config.backend_url
    deep_llm = create_llm_client(
        provider, config.deep_think_llm, backend_url, **llm_kwargs
    ).get_llm()
    quick_llm = create_llm_client(
        provider, config.quick_think_llm, backend_url, **llm_kwargs
    ).get_llm()
    return deep_llm, quick_llm
