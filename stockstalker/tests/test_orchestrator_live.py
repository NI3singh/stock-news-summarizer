"""StockStalker v2 — live orchestrator integration test (real scrape + Gemini).

Marked ``live`` (deselected by default). Run:
    pytest stockstalker/tests/test_orchestrator_live.py -v -m live -s
Requires real GEMINI_API_KEY + POLYGON_API_KEY in .env.
"""
import asyncio
import time

import aiosqlite
import pytest

from stockstalker.agents import OrchestratorAgent
from stockstalker.llm import GeminiClient
from stockstalker.memory import DatabaseManager, VectorStore
from stockstalker.scrapers import ScraperOrchestrator
from stockstalker.schemas import AgentContext, TickerAnalysis

pytestmark = pytest.mark.live


async def test_full_orchestrator_pipeline():
    db = DatabaseManager()
    await db.init_db()
    vs = VectorStore()
    llm = GeminiClient()
    orch_scraper = ScraperOrchestrator()
    agent = OrchestratorAgent("orchestrator", llm, db, vs)

    # Step 1 — scrape
    articles = await orch_scraper.scrape_all("AAPL")
    assert len(articles) > 0, "Need at least 1 article to proceed"
    print(f"Scraped {len(articles)} articles")

    # Step 2 — run orchestrator
    start = time.time()
    ctx = AgentContext(ticker="AAPL", articles=articles)
    result = await agent.execute(ctx)
    elapsed = time.time() - start
    print(f"Orchestrator completed in {elapsed:.1f}s")

    # Step 3 — validate result
    assert result.success is True, f"Orchestrator failed: {result.error}"
    ta = result.data
    assert isinstance(ta, TickerAnalysis)
    assert ta.ticker == "AAPL"
    assert ta.news is not None
    assert len(ta.final_synthesis) > 100
    assert ta.memory is not None
    print(f"Sentiment: {ta.news.sentiment_score}")
    print(f"Synthesis: {ta.final_synthesis[:200]}")

    # Step 4 — DB persistence
    analyses = await db.get_recent_analyses("AAPL", days=1)
    assert len(analyses) >= 1, "Analysis should have been saved to DB"
    print(f"DB analyses count: {len(analyses)}")

    # Step 5 — vector store indexing
    await asyncio.sleep(0.5)
    vs_size = await vs.collection_size()
    assert vs_size > 0, "Articles should have been indexed in ChromaDB"
    print(f"Vector store size: {vs_size}")

    # Step 6 — agent_runs log
    async with aiosqlite.connect(db.db_path) as conn:
        async with conn.execute(
            "SELECT agent_name, success, duration_seconds FROM agent_runs "
            "WHERE ticker='AAPL' ORDER BY id DESC LIMIT 10"
        ) as cur:
            rows = await cur.fetchall()

    print("agent_runs (last 10):")
    for name, success, dur in rows:
        dur_str = f"{dur:.2f}s" if dur is not None else "NULL"
        print(f"  {name}: success={success} duration={dur_str}")

    agent_names = {row[0] for row in rows}
    for expected in ("memory_agent", "news_agent", "quant_agent", "orchestrator"):
        assert expected in agent_names, f"{expected} not found in agent_runs"

    print("Orchestrator integration test PASSED")
