"""QuantMind v2 — Gemini LLM client (core async wrapper).

The pipeline's single high-level entry point for Gemini calls. Built on the
committed LangChain factory (kept for multi-provider flexibility) instead of
importing ``google.generativeai`` directly: it instantiates the Gemini chat model
via ``create_llm_client("google", ...)`` and layers on the "serious" concerns —
rate-limit integration, exponential-backoff retry, and token/char logging.
"""
import asyncio
from typing import Type, TypeVar

from quantmind.config import settings
from quantmind.llm.factory import create_llm_client
from quantmind.utils import gemini_limiter, logger

T = TypeVar("T")


class LLMError(Exception):
    """Raised when an LLM call fails (e.g. after exhausting retries)."""


class LLMStructuredOutputError(LLMError):
    """Raised when structured output cannot be produced/validated (Step 3.19)."""


class GeminiClient:
    """High-level async Gemini wrapper: retry + rate-limit + logging."""

    def __init__(self, model: str | None = None) -> None:
        # Built via the LangChain factory (google provider) — no direct
        # google.generativeai import. The API key is read from GEMINI_API_KEY
        # (loaded into os.environ at package import).
        self.model = create_llm_client(
            "google", model or settings.quick_think_llm
        ).get_llm()
        self._gemini_limiter = gemini_limiter

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate plain text with rate-limiting and exponential-backoff retry."""
        content = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        max_attempts = 3

        async with self._gemini_limiter:
            for attempt in range(1, max_attempts + 1):
                try:
                    response = await self.model.ainvoke(content)
                    text = (
                        response.content
                        if isinstance(response.content, str)
                        else str(response.content)
                    )
                    logger.info(
                        "agent=gemini prompt_chars={} response_chars={} attempt={}",
                        len(prompt),
                        len(text),
                        attempt,
                    )
                    return text.strip()
                except Exception as exc:  # noqa: BLE001 — retry on any provider error
                    if attempt < max_attempts:
                        delay = 2 * (2 ** (attempt - 1))  # 2s, then 4s
                        logger.warning(
                            "gemini attempt {} failed ({}); retrying in {}s",
                            attempt,
                            exc,
                            delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "gemini failed after {} attempts: {}", max_attempts, exc
                        )
                        raise LLMError(
                            f"Gemini generate_text failed after {max_attempts} attempts: {exc}"
                        ) from exc

        # Defensive: the loop above always returns or raises.
        raise LLMError("Gemini generate_text: unexpected control flow")

    async def generate_structured(
        self, prompt: str, schema: Type[T], system_prompt: str | None = None
    ) -> T:
        """Return a validated Pydantic instance of ``schema`` from the model.

        Uses LangChain's ``.with_structured_output(schema)`` (kept-LangChain
        decision) so the model returns a validated object DIRECTLY — no JSON
        string parsing, fence stripping, or response_mime_type juggling. Shares
        the rate-limit + exponential-backoff retry behaviour of generate_text.
        """
        content = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        structured_model = self.model.with_structured_output(schema)
        max_attempts = 3

        async with self._gemini_limiter:
            for attempt in range(1, max_attempts + 1):
                try:
                    result = await structured_model.ainvoke(content)
                    if not isinstance(result, schema):
                        # Defensive: coerce a dict-like result into the model.
                        result = schema.model_validate(result)
                    logger.info(
                        "agent=gemini schema={} attempt={}", schema.__name__, attempt
                    )
                    return result
                except Exception as exc:  # noqa: BLE001 — retry on any provider/parse error
                    if attempt < max_attempts:
                        delay = 2 * (2 ** (attempt - 1))  # 2s, then 4s
                        logger.warning(
                            "gemini structured attempt {} failed ({}); retrying in {}s",
                            attempt,
                            exc,
                            delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "gemini structured output failed after {} attempts: {}",
                            max_attempts,
                            exc,
                        )
                        raise LLMStructuredOutputError(
                            f"Failed to produce {schema.__name__}: {exc}"
                        ) from exc

        # Defensive: the loop above always returns or raises.
        raise LLMStructuredOutputError(
            f"Generate structured ({schema.__name__}): unexpected control flow"
        )
