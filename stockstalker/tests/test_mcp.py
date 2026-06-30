"""StockStalker — MCP tool unit tests (mocked PipelineRunner; no server, no network).

Each tool reads through get_runner(), so the tests inject a stub runner via
set_runner() and assert on the returned dicts.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

from stockstalker.integrations.mcp_server import (
    compare_tickers,
    get_stock_analysis,
    get_system_status,
    get_watchlist,
    set_runner,
)


def _runner(tickers, analyses_by_ticker=None, vector_size=0):
    """Build a stub runner with the db / vector_store methods the tools call."""
    db = SimpleNamespace()
    db.get_active_tickers = AsyncMock(return_value=tickers)
    if analyses_by_ticker is not None:
        def _gra(user_id, ticker, days=1):
            return analyses_by_ticker.get(ticker, [])
        db.get_recent_analyses = AsyncMock(side_effect=_gra)
    else:
        db.get_recent_analyses = AsyncMock(return_value=[])
    vs = SimpleNamespace(collection_size=AsyncMock(return_value=vector_size))
    return SimpleNamespace(db=db, vector_store=vs)


# Test 1 — get_watchlist with data
async def test_get_watchlist_with_data():
    set_runner(
        _runner(
            ["AAPL", "MSFT"],
            {
                "AAPL": [{"sentiment_score": 0.7, "analyzed_at": "2026-06-24T10:00:00"}],
                "MSFT": [{"sentiment_score": -0.5, "analyzed_at": "2026-06-24T10:00:00"}],
            },
        )
    )
    res = await get_watchlist()
    assert res["count"] == 2
    assert isinstance(res["most_bullish"], str)
    assert res["most_bullish"] == "AAPL"
    for entry in res["tickers"]:
        for key in ("ticker", "sentiment_score", "sentiment_label", "last_analyzed"):
            assert key in entry


# Test 2 — get_watchlist empty
async def test_get_watchlist_empty():
    set_runner(_runner([]))
    res = await get_watchlist()
    assert res["tickers"] == []
    assert res["count"] == 0


# Test 3 — compare_tickers ranks by sentiment
async def test_compare_tickers():
    set_runner(
        _runner(
            [],
            {
                "AAPL": [{"sentiment_score": 0.7, "what_changed": "up", "analyzed_at": "x"}],
                "MSFT": [{"sentiment_score": -0.5, "what_changed": "down", "analyzed_at": "x"}],
            },
        )
    )
    res = await compare_tickers(["AAPL", "MSFT"])
    assert len(res["ranking_by_sentiment"]) == 2
    assert res["strongest_buy_signal"] == "AAPL"
    assert res["strongest_sell_signal"] == "MSFT"


# Test 4 — compare_tickers exceeds the limit
async def test_compare_tickers_exceeds_limit():
    set_runner(_runner([]))
    res = await compare_tickers(["A", "B", "C", "D", "E", "F"])
    assert "error" in res


# Test 5 — get_stock_analysis with no data
async def test_get_stock_analysis_no_data():
    set_runner(_runner([]))  # get_recent_analyses -> []
    res = await get_stock_analysis("AAPL")
    assert "error" in res
    assert "suggestion" in res


# Test 6 — get_system_status structure
async def test_get_system_status():
    set_runner(_runner(["AAPL"], vector_size=42))
    res = await get_system_status()
    assert res["status"] == "operational"
    assert "active_tickers" in res
    assert "scheduler_time" in res
