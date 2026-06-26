"""StockStalker v2 — LLM client base class + content normalization.

Provider-agnostic surface: every concrete client returns a ready-to-use LangChain
chat object via ``get_llm()``. ``normalize_content()`` collapses list-of-typed-blocks
content (Reasoning / Responses API, Gemini 3) down to a plain string so every
downstream consumer sees the same ``.content`` shape.
"""
import warnings
from abc import ABC, abstractmethod
from typing import Any


def normalize_content(response):
    """Collapse list-of-typed-blocks ``.content`` to a single string (in place)."""
    content = getattr(response, "content", None)
    if isinstance(content, list):
        texts = [
            item.get("text", "")
            if isinstance(item, dict) and item.get("type") == "text"
            else item
            if isinstance(item, str)
            else ""
            for item in content
        ]
        response.content = "\n".join(t for t in texts if t)
    return response


class BaseLLMClient(ABC):
    """Abstract base for every provider client."""

    def __init__(self, model: str, base_url: str | None = None, **kwargs: Any) -> None:
        self.model = model
        self.base_url = base_url
        self.kwargs = kwargs  # passthrough bag, forwarded to the SDK constructor

    def get_provider_name(self) -> str:
        return self.__class__.__name__.replace("Client", "").lower()

    def warn_if_unknown_model(self) -> None:
        """Warn (never fail) when the model id is not in the known catalog."""
        if not self.validate_model():
            warnings.warn(
                f"Unknown model '{self.model}' for provider "
                f"'{self.get_provider_name()}'; proceeding anyway.",
                RuntimeWarning,
                stacklevel=2,
            )

    @abstractmethod
    def get_llm(self) -> Any:
        """Return a ready-to-use LangChain chat model instance."""

    @abstractmethod
    def validate_model(self) -> bool:
        """Return True if the model id is recognised (or validation is not applicable)."""
