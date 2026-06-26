"""StockStalker v2 — provider → API-key env-var map (single source of truth).

The one place that knows which environment variable holds each provider's key,
consulted by the clients (to read the key). ``None`` means the provider has no
single API key (Ollama is local; local OpenAI-compatible servers use a
placeholder key).
"""

# NOTE: 'google' maps to GEMINI_API_KEY to reuse StockStalker's existing key — the
# Google client forwards it to LangChain as ``google_api_key``.
PROVIDER_API_KEY_ENV: dict[str, str | None] = {
    "google": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "xai": "XAI_API_KEY",
    "ollama": None,  # local, no auth
    "openai_compatible": "OPENAI_COMPATIBLE_API_KEY",
}


def get_api_key_env(provider: str) -> str | None:
    """Return the env-var name holding the provider's key, or None if keyless."""
    return PROVIDER_API_KEY_ENV.get(provider.lower())
