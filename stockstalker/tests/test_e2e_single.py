"""StockStalker v2 — end-to-end single-ticker demo test (the primary portfolio demo).

Marked ``live``. Run: pytest stockstalker/tests/test_e2e_single.py -v -m live -s
Drives the full PipelineRunner on AAPL and prints a complete, readable analysis:
scrape -> memory -> news + quant -> synthesis -> persist, with timing.
"""
import sys
import time

import aiosqlite
import pytest

from stockstalker.config.settings import DEV_UID
from stockstalker.pipeline import PipelineRunner
from stockstalker.schemas import TickerAnalysis

# The synthesis/summary are LLM-generated and may contain non-cp1252 characters
# (em-dashes, curly quotes); make the demo print survive a Windows pipe.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):  # pragma: no cover — non-reconfigurable stream
    pass

pytestmark = pytest.mark.live


async def test_single_ticker_full_pipeline():
    runner = PipelineRunner()
    await runner.initialize()

    # --- Run the full pipeline ---
    start = time.time()
    ta = await runner.analyze_ticker(DEV_UID, "AAPL")
    elapsed = time.time() - start

    # --- Type validation ---
    assert isinstance(ta, TickerAnalysis), f"Expected TickerAnalysis, got {type(ta)}"
    assert ta.ticker == "AAPL"

    # --- Field completeness ---
    assert len(ta.final_synthesis) > 100, "Synthesis too short"
    assert len(ta.news.summary) > 100, "News summary too short"
    assert len(ta.news.key_themes) >= 2, "Need at least 2 themes"
    assert -1.0 <= ta.news.sentiment_score <= 1.0

    # --- DB persistence ---
    analyses = await runner.db.get_recent_analyses(DEV_UID, "AAPL", days=1)
    assert len(analyses) >= 1, "Analysis should be in DB"

    # --- Vector store persistence ---
    vs_size = await runner.vector_store.collection_size()
    assert vs_size > 0, "Articles should be in vector store"

    # --- Agent run logs: all four agents must have executed and logged ---
    runs = await runner.db.get_agent_runs(DEV_UID, limit=200)
    agent_names = {r["agent_name"] for r in runs if r["ticker"] == "AAPL"}
    for expected in ("memory_agent", "news_agent", "quant_agent", "orchestrator"):
        assert expected in agent_names, f"{expected} missing from agent_runs"

    # --- Performance ---
    assert elapsed < 90.0, f"Pipeline too slow: {elapsed:.1f}s"

    # --- Formatted demo output ---
    print("\n" + "=" * 60)
    print(f"TICKER: {ta.ticker}  |  {ta.analyzed_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"Elapsed: {elapsed:.1f}s")
    print(f"Articles scraped: {len(ta.news.selected_articles)}")
    print(f"Sentiment: {ta.news.sentiment_score:+.2f}")
    print(f"Themes: {', '.join(ta.news.key_themes)}")
    print(f"\nWHAT CHANGED:\n{ta.news.what_changed}")
    print(f"\nSYNTHESIS:\n{ta.final_synthesis}")
    if ta.quant:
        print(
            f"\nSIGNALS: RSI={ta.quant.signals.rsi}  Vol%={ta.quant.signals.volume_ratio}"
        )
    print("=" * 60)
    print("E2E single ticker test PASSED")
