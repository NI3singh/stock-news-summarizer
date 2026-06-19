"""QuantMind v2 — LLM module tests (provider-agnostic factory).

Exercise construction / dispatch / registry / capability logic only — no live API
calls — so they run without real provider keys (the placeholder GEMINI_API_KEY
loaded from .env is enough to construct the Google client).
"""
import subprocess
import sys
from pathlib import Path

import pytest

from quantmind.llm import BaseLLMClient, create_llm_client
from quantmind.llm.anthropic_client import AnthropicClient
from quantmind.llm.base_client import normalize_content
from quantmind.llm.capabilities import get_capabilities
from quantmind.llm.google_client import GoogleClient
from quantmind.llm.openai_client import OpenAIClient, is_openai_compatible
from quantmind.schemas import TechnicalSignals

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_lazy_imports_no_sdk():
    """`import quantmind.llm` must NOT pull any LangChain provider SDK (gotcha #8).

    Run in a fresh subprocess so other tests loading LangChain can't pollute it.
    """
    code = (
        "import sys, quantmind.llm; "
        "loaded=[m for m in ('langchain_openai','langchain_google_genai','langchain_anthropic') "
        "if m in sys.modules]; "
        "assert not loaded, loaded"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
    )
    assert result.returncode == 0, result.stderr


def test_factory_dispatch():
    assert isinstance(create_llm_client("google", "gemini-2.5-flash"), GoogleClient)
    assert isinstance(create_llm_client("anthropic", "claude-opus-4-5"), AnthropicClient)
    for provider in ("ollama", "openrouter", "deepseek", "xai", "groq", "openai"):
        assert isinstance(create_llm_client(provider, "m"), OpenAIClient)
    assert isinstance(create_llm_client("google", "m"), BaseLLMClient)


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        create_llm_client("does-not-exist", "m")


def test_registry_membership():
    assert is_openai_compatible("openai")
    assert is_openai_compatible("ollama")
    assert not is_openai_compatible("google")


def test_capabilities():
    assert get_capabilities("some-new-model").preferred_structured_method == "function_calling"
    deepseek = get_capabilities("deepseek-reasoner")
    assert deepseek.supports_tool_choice is False
    assert deepseek.preferred_structured_method == "json_mode"


def test_normalize_content_collapses_blocks():
    class Resp:
        content = [
            {"type": "text", "text": "hello"},
            {"type": "thinking", "text": "secret"},
            "world",
        ]

    assert normalize_content(Resp()).content == "hello\nworld"


def _base_url_of(llm):
    return getattr(llm, "openai_api_base", None) or getattr(llm, "base_url", None)


def test_base_url_precedence(monkeypatch):
    """explicit > base_url_env > spec default (gotcha #1)."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    assert _base_url_of(create_llm_client("ollama", "m").get_llm()) == "http://localhost:11434/v1"

    explicit = create_llm_client("ollama", "m", base_url="http://explicit:9/v1").get_llm()
    assert _base_url_of(explicit) == "http://explicit:9/v1"

    monkeypatch.setenv("OLLAMA_BASE_URL", "http://envhost:1/v1")
    assert _base_url_of(create_llm_client("ollama", "m").get_llm()) == "http://envhost:1/v1"


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        create_llm_client("openai", "gpt-x").get_llm()


def test_require_base_url_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_COMPATIBLE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        create_llm_client("openai_compatible", "m").get_llm()


def test_keyless_placeholder(monkeypatch):
    """A keyless local server constructs via the placeholder key (gotcha #3)."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    assert create_llm_client("ollama", "m").get_llm() is not None


def test_structured_output_binding():
    bound = create_llm_client("ollama", "m").get_llm().with_structured_output(TechnicalSignals)
    assert bound is not None


def test_native_clients_construct():
    """Google (placeholder GEMINI key from .env) and Anthropic (explicit key) construct."""
    assert create_llm_client("google", "gemini-2.5-flash").get_llm() is not None
    assert (
        create_llm_client("anthropic", "claude-opus-4-5", api_key="sk-ant-placeholder").get_llm()
        is not None
    )


def test_build_llms_from_config():
    """The config -> LLM bridge (§4.11) builds deep + quick models from Settings."""
    from quantmind.llm.builder import build_llms, get_provider_kwargs

    assert isinstance(get_provider_kwargs(), dict)
    deep, quick = build_llms()
    assert deep is not None
    assert quick is not None
