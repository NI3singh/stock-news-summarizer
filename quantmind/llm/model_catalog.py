"""QuantMind v2 — model catalog (known-model sets; CLI dropdown source).

``MODEL_OPTIONS`` maps provider -> {"deep": [(label, id)...], "quick": [...]}.
Providers absent from this map accept any model id (validation stays permissive),
so we only list the ones we want to soft-validate (currently Google/Gemini).
"""

MODEL_OPTIONS: dict[str, dict[str, list[tuple[str, str]]]] = {
    "google": {
        "deep": [
            ("Gemini 2.5 Pro", "gemini-2.5-pro"),
            ("Gemini 2.5 Flash", "gemini-2.5-flash"),
        ],
        "quick": [
            ("Gemini 2.5 Flash", "gemini-2.5-flash"),
            ("Gemini 2.5 Flash Lite", "gemini-2.5-flash-lite"),
        ],
    },
}


def has_catalog(provider: str) -> bool:
    """True if we maintain a fixed model catalog for this provider."""
    return provider.lower() in MODEL_OPTIONS


def get_known_models(provider: str | None = None) -> set[str]:
    """Flat set of known model ids (optionally restricted to one provider)."""
    known: set[str] = set()
    providers = [provider.lower()] if provider else list(MODEL_OPTIONS)
    for p in providers:
        for options in MODEL_OPTIONS.get(p, {}).values():
            known.update(model_id for _label, model_id in options)
    return known
