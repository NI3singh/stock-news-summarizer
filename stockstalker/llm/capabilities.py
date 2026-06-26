"""StockStalker v2 — per-model capability table (single source of truth for quirks).

Keyed by model id: exact match first, then regex patterns (forward-compat), then a
permissive default. The structured-output dispatch reads this table instead of
hardcoding model names, so a new model quirk is just one data row.
"""
import re
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ModelCapabilities:
    supports_tool_choice: bool
    supports_json_mode: bool
    supports_json_schema: bool
    preferred_structured_method: Literal[
        "function_calling", "json_mode", "json_schema", "none"
    ]
    requires_reasoning_content_roundtrip: bool = False
    requires_reasoning_split: bool = False


# Permissive default: most models do function-calling structured output fine.
_DEFAULT = ModelCapabilities(
    supports_tool_choice=True,
    supports_json_mode=True,
    supports_json_schema=True,
    preferred_structured_method="function_calling",
)

# DeepSeek reasoner: rejects tool_choice; round-trips reasoning_content.
_DEEPSEEK_THINKING = ModelCapabilities(
    supports_tool_choice=False,
    supports_json_mode=True,
    supports_json_schema=False,
    preferred_structured_method="json_mode",
    requires_reasoning_content_roundtrip=True,
)

_BY_ID: dict[str, ModelCapabilities] = {
    "deepseek-reasoner": _DEEPSEEK_THINKING,
}

_BY_PATTERN: list[tuple[re.Pattern, ModelCapabilities]] = [
    (re.compile(r"^deepseek-r\d"), _DEEPSEEK_THINKING),  # forward-compat
]


def get_capabilities(model_name: str) -> ModelCapabilities:
    """Resolve capabilities for a model id: exact id > regex pattern > default."""
    if model_name in _BY_ID:
        return _BY_ID[model_name]
    for pattern, caps in _BY_PATTERN:
        if pattern.match(model_name):
            return caps
    return _DEFAULT
