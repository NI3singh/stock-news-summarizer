"""QuantMind v2 — model validation (drives warnings only, never hard failure).

Unknown models still run — new models ship faster than catalogs update.
"""
from quantmind.llm.model_catalog import get_known_models, has_catalog

# Providers that accept any model id (no fixed catalog of names).
_ANY_MODEL_PROVIDERS = {
    "ollama",
    "openrouter",
    "openai_compatible",
    "deepseek",
    "xai",
    "groq",
}


def validate_model(provider: str, model: str) -> bool:
    """True if the model is recognised or validation is not applicable."""
    p = provider.lower()
    if p in _ANY_MODEL_PROVIDERS:
        return True
    if not has_catalog(p):
        return True  # no catalog for this provider -> stay permissive
    return model in get_known_models(p)
