"""StockStalker v2 — agent unit tests (fully mocked; no real LLM / network).

Mocks target the LangChain-backed client surface (generate_text /
generate_structured) and the DB/VectorStore async methods; yfinance.download is
patched for the Quant Agent.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from stockstalker.agents import BaseAgent, MemoryAgent, NewsAgent, QuantAgent
from stockstalker.schemas import (
    AgentContext,
    AgentResult,
    Article,
    MemoryContext,
    NewsAnalysis,
    QuantAnalysis,
    TechnicalSignals,
)


@pytest.fixture
def mocks():
    """Mocked GeminiClient / DatabaseManager / VectorStore with sensible defaults."""
    llm = MagicMock()
    llm.generate_text = AsyncMock(return_value="[1, 2, 3]")
    llm.generate_structured = AsyncMock(return_value=MemoryContext())

    db = MagicMock()
    db.log_agent_run = AsyncMock(return_value=None)
    db.get_recent_analyses = AsyncMock(return_value=[])
    db.save_analysis = AsyncMock(return_value=None)

    vs = MagicMock()
    vs.search_similar = AsyncMock(return_value=["Past event: Apple beat earnings"])
    vs.add_articles = AsyncMock(return_value=None)

    return SimpleNamespace(llm=llm, db=db, vs=vs)


# --- Memory Agent ---
async def test_memory_agent_returns_correct_type(mocks):
    mocks.vs.search_similar = AsyncMock(return_value=["event1", "event2"])
    mocks.db.get_recent_analyses = AsyncMock(
        return_value=[{"sentiment_score": 0.5}, {"sentiment_score": 0.3}]
    )
    agent = MemoryAgent("memory_agent", mocks.llm, mocks.db, mocks.vs)
    result = await agent.execute(AgentContext(ticker="AAPL"))
    assert result.success is True
    assert isinstance(result.data, MemoryContext)
    assert result.data.days_of_history == 2
    assert "event1" in result.data.similar_past_events


async def test_memory_agent_empty_db_returns_zero_history(mocks):
    mocks.vs.search_similar = AsyncMock(return_value=[])
    mocks.db.get_recent_analyses = AsyncMock(return_value=[])
    agent = MemoryAgent("memory_agent", mocks.llm, mocks.db, mocks.vs)
    result = await agent.execute(AgentContext(ticker="AAPL"))
    assert result.data.days_of_history == 0
    assert result.data.similar_past_events == []


# --- News Agent ---
async def test_news_agent_no_articles_returns_failure(mocks):
    agent = NewsAgent("news_agent", mocks.llm, mocks.db, mocks.vs)
    result = await agent.execute(AgentContext(ticker="AAPL", articles=[]))
    assert result.success is False
    assert "No articles" in result.error


async def test_news_agent_returns_news_analysis(mocks):
    articles = [
        Article(title="Apple Earnings", url="https://t.co/1", source="T", ticker="AAPL")
    ]
    mocks.llm.generate_text = AsyncMock(return_value="[1]")
    mocks.llm.generate_structured = AsyncMock(
        return_value=NewsAnalysis(
            sentiment_score=0.7, summary="Strong results", key_themes=["earnings"]
        )
    )
    agent = NewsAgent("news_agent", mocks.llm, mocks.db, mocks.vs)
    result = await agent.execute(AgentContext(ticker="AAPL", articles=articles))
    assert result.success is True
    assert isinstance(result.data, NewsAnalysis)
    assert result.data.sentiment_score == 0.7


# --- Quant Agent ---
async def test_quant_agent_invalid_ticker_returns_failure(mocks, mocker):
    mocker.patch("yfinance.download", return_value=pd.DataFrame())
    agent = QuantAgent("quant_agent", mocks.llm, mocks.db, mocks.vs)
    result = await agent.execute(AgentContext(ticker="ZZZZ", memory=MemoryContext()))
    assert result.success is False
    assert result.error is not None


async def test_quant_agent_returns_quant_analysis(mocks, mocker):
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    close = [100 + i * 0.5 + (i % 5) for i in range(60)]
    df = pd.DataFrame(
        {
            "Open": [c - 1 for c in close],
            "High": [c + 2 for c in close],
            "Low": [c - 2 for c in close],
            "Close": close,
            "Volume": [1_000_000 + i * 10_000 for i in range(60)],
        },
        index=dates,
    )
    mocker.patch("yfinance.download", return_value=df)
    mocks.llm.generate_structured = AsyncMock(
        return_value=QuantAnalysis(
            signals=TechnicalSignals(rsi=65.0), interpretation="Bullish momentum"
        )
    )
    agent = QuantAgent("quant_agent", mocks.llm, mocks.db, mocks.vs)
    result = await agent.execute(AgentContext(ticker="AAPL", memory=MemoryContext()))
    assert result.success is True
    assert isinstance(result.data, QuantAnalysis)


# --- Base Agent ---
async def test_execute_populates_duration(mocks):
    class _OkAgent(BaseAgent):
        async def run(self, context):
            return AgentResult(agent_name="test", success=True)

    agent = _OkAgent("test", mocks.llm, mocks.db, mocks.vs)
    result = await agent.execute(AgentContext(ticker="AAPL"))
    assert result.duration_seconds > 0


async def test_execute_catches_exceptions(mocks):
    class _BoomAgent(BaseAgent):
        async def run(self, context):
            raise RuntimeError("test error")

    agent = _BoomAgent("test", mocks.llm, mocks.db, mocks.vs)
    result = await agent.execute(AgentContext(ticker="AAPL"))
    assert result.success is False
    assert "test error" in result.error
