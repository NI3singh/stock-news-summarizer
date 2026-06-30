"""StockStalker v2 — Phase 1 foundation smoke tests.

Verifies that every foundation component imports, initialises, and performs its
most basic operation without error. Async tests rely on pytest-asyncio with
``asyncio_mode = "auto"`` (configured in pyproject.toml).

NOTE: the DB tests use a pytest ``tmp_path`` file rather than ``:memory:`` —
``DatabaseManager`` opens a new connection per operation, and each
``aiosqlite.connect(":memory:")`` is a separate, throwaway in-memory database,
so tables created in ``init_db()`` would not survive to the next call.
"""
import time

import aiosqlite

from stockstalker.config import Settings, settings
from stockstalker.utils import (
    AsyncRateLimiter,
    gemini_limiter,
    polygon_limiter,
    scraper_limiter,
    logger,
)
from stockstalker.schemas import (
    Article,
    TechnicalSignals,
    MemoryContext,
    NewsAnalysis,
    QuantAnalysis,
    TickerAnalysis,
    AgentContext,
    AgentResult,
)
from stockstalker.memory import DatabaseManager, VectorStore


def test_imports_resolve():
    """Test 1 — every module/class/singleton imports without error."""
    assert Settings is not None
    assert settings is not None
    assert logger is not None
    for model in (
        Article, TechnicalSignals, MemoryContext, NewsAnalysis,
        QuantAnalysis, TickerAnalysis, AgentContext, AgentResult,
    ):
        assert model is not None
    assert DatabaseManager is not None
    assert VectorStore is not None
    assert AsyncRateLimiter is not None
    for limiter in (gemini_limiter, polygon_limiter, scraper_limiter):
        assert isinstance(limiter, AsyncRateLimiter)


def test_settings_loads():
    """Test 2 — Settings loads and basic fields are valid."""
    s = Settings()
    assert isinstance(s.timezone, str) and s.timezone != ""
    assert isinstance(s.max_concurrent_tickers, int)
    assert s.max_concurrent_tickers > 0
    assert s.gemini_api_key != ""  # placeholder value from .env


async def test_database_tables(tmp_path):
    """Test 3 — init_db() creates all four tables."""
    db = DatabaseManager(db_path=str(tmp_path / "test.db"))
    await db.init_db()
    async with aiosqlite.connect(db.db_path) as conn:
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ) as cursor:
            names = {row[0] for row in await cursor.fetchall()}
    assert {"tickers", "articles", "analyses", "agent_runs"} <= names


async def test_ticker_crud(tmp_path):
    """Test 4 — add / list / deactivate ticker lifecycle."""
    db = DatabaseManager(db_path=str(tmp_path / "test.db"))
    await db.init_db()
    assert await db.add_ticker("AAPL") is True
    assert await db.add_ticker("AAPL") is False  # duplicate
    assert "AAPL" in await db.get_active_tickers()
    await db.deactivate_ticker("AAPL")
    assert "AAPL" not in await db.get_active_tickers()


async def test_vectorstore_init(tmp_path, monkeypatch):
    """Test 5 — VectorStore starts empty, accepts an article, reports size."""
    from stockstalker.memory import vector_store as vs_mod

    async def _fake_embed(texts, task_type):  # keep this foundation test offline/fast
        return [[0.1] * vs_mod.EMBED_DIM for _ in texts]

    monkeypatch.setattr(vs_mod, "_embed", _fake_embed)

    vs = VectorStore(db_url=str(tmp_path / "vec.db"))  # local SQLite (JSON-cosine path)
    assert await vs.collection_size() == 0
    await vs.add_articles(
        [
            Article(
                title="Test article",
                url="https://example.com/x",
                source="Test",
                ticker="AAPL",
                content="A sufficiently long article body for embedding.",
            )
        ]
    )
    assert await vs.collection_size() == 1


def test_all_models_instantiate():
    """Test 6 — every model instantiates with minimal valid data."""
    article = Article(title="t", url="https://e.com", source="s", ticker="AAPL")
    signals = TechnicalSignals()
    memory = MemoryContext()
    news = NewsAnalysis()
    quant = QuantAnalysis(signals=signals)
    ticker_analysis = TickerAnalysis(ticker="AAPL", news=news, memory=memory)
    ctx = AgentContext(ticker="AAPL")
    result = AgentResult(agent_name="a", success=True)

    assert isinstance(article, Article)
    assert isinstance(signals, TechnicalSignals)
    assert isinstance(memory, MemoryContext)
    assert isinstance(news, NewsAnalysis)
    assert isinstance(quant, QuantAnalysis)
    assert isinstance(ticker_analysis, TickerAnalysis)
    assert isinstance(ctx, AgentContext)
    assert isinstance(result, AgentResult)


async def test_rate_limiter_callable():
    """Test 7 — gemini_limiter.acquire() completes quickly on first call."""
    start = time.monotonic()
    await gemini_limiter.acquire()
    assert (time.monotonic() - start) < 2.0
