"""StockStalker v2 — LLM client unit tests (fully mocked; no real API calls).

Adapted to the LangChain-backed GeminiClient (the keep-LangChain decision): the
client calls ``self.model.ainvoke`` (not ``generate_content``) and gets structured
output via ``self.model.with_structured_output(schema).ainvoke`` (not ``.text``
JSON parsing). The tests mock those and verify the same intents: retry/backoff,
LLMError on exhaustion, structured Pydantic typing, structured failure handling,
dict coercion, and rate-limiter usage.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from google.api_core.exceptions import ResourceExhausted

from stockstalker.llm import GeminiClient, LLMError, LLMStructuredOutputError
from stockstalker.schemas import MemoryContext
from stockstalker.utils import gemini_limiter


@pytest.fixture(autouse=True)
def mock_acquire(mocker):
    """Replace the global rate-limiter's acquire with a no-op AsyncMock for every
    test (keeps tests fast, isolated, and free of cross-event-loop lock issues).
    Returned so Test 6 can assert it was called."""
    return mocker.patch.object(gemini_limiter, "acquire", new=AsyncMock())


def _make_client(mocker, mock_model):
    """Build a GeminiClient whose underlying model is the given mock (no real
    factory/model construction, so no API key or network is needed)."""
    fake_factory_client = MagicMock()
    fake_factory_client.get_llm.return_value = mock_model
    mocker.patch(
        "stockstalker.llm.client.create_llm_client", return_value=fake_factory_client
    )
    return GeminiClient()


# --- Test 1: retry on failure then success ---
async def test_retry_then_success(mocker):
    mocker.patch("asyncio.sleep", new=AsyncMock())  # skip the 2s/4s backoff
    ok = MagicMock()
    ok.content = "FINAL_RESPONSE"
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(
        side_effect=[ResourceExhausted("429"), ResourceExhausted("429"), ok]
    )
    client = _make_client(mocker, mock_model)

    result = await client.generate_text("test prompt")

    assert result == "FINAL_RESPONSE"
    assert mock_model.ainvoke.call_count == 3


# --- Test 2: total failure raises LLMError ---
async def test_total_failure_raises_llmerror(mocker):
    mocker.patch("asyncio.sleep", new=AsyncMock())
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(side_effect=ResourceExhausted("429"))
    client = _make_client(mocker, mock_model)

    with pytest.raises(LLMError):
        await client.generate_text("test prompt")
    assert mock_model.ainvoke.call_count == 3


# --- Test 3: generate_structured returns the correct Pydantic type ---
async def test_generate_structured_returns_pydantic(mocker):
    expected = MemoryContext(
        similar_past_events=["Apple earnings beat"],
        historical_sentiment_trend="Positive",
        days_of_history=3,
    )
    structured = MagicMock()
    structured.ainvoke = AsyncMock(return_value=expected)
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = structured
    client = _make_client(mocker, mock_model)

    result = await client.generate_structured("test prompt", MemoryContext)

    assert isinstance(result, MemoryContext)
    assert result.days_of_history == 3
    assert result.historical_sentiment_trend == "Positive"


# --- Test 4: generate_structured raises on structured-output failure ---
async def test_generate_structured_raises_on_failure(mocker):
    mocker.patch("asyncio.sleep", new=AsyncMock())
    structured = MagicMock()
    structured.ainvoke = AsyncMock(side_effect=ValueError("could not parse structured output"))
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = structured
    client = _make_client(mocker, mock_model)

    with pytest.raises(LLMStructuredOutputError):
        await client.generate_structured("test prompt", MemoryContext)


# --- Test 5: generate_structured coerces a dict result into the model ---
# (LangChain analog of the step's markdown-fence test: with_structured_output
# returns parsed objects, so there's no fenced text; instead we verify the
# defensive `schema.model_validate` path when a dict comes back.)
async def test_generate_structured_coerces_dict(mocker):
    structured = MagicMock()
    structured.ainvoke = AsyncMock(
        return_value={
            "similar_past_events": [],
            "historical_sentiment_trend": "Neutral",
            "days_of_history": 0,
        }
    )
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = structured
    client = _make_client(mocker, mock_model)

    result = await client.generate_structured("test prompt", MemoryContext)

    assert isinstance(result, MemoryContext)
    assert result.historical_sentiment_trend == "Neutral"


# --- Test 6: the rate limiter is acquired ---
async def test_rate_limiter_acquire_called(mocker, mock_acquire):
    ok = MagicMock()
    ok.content = "ok"
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(return_value=ok)
    client = _make_client(mocker, mock_model)

    await client.generate_text("test prompt")

    assert mock_acquire.called
