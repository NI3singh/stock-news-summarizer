"""QuantMind v2 — Memory RAG loop test (proves cross-run learning).

Marked ``live``. Run: pytest quantmind/tests/test_memory_rag.py -v -m live -s
Run 1 on a fresh ticker (NVDA) has no history; Run 2 must retrieve Run 1's
analysis (SQLite) and indexed articles (ChromaDB) — proving the RAG loop.
NOTE: not idempotent — Run 1 asserts NVDA is fresh, so it expects a clean store.
"""
import asyncio

import pytest

from quantmind.agents import OrchestratorAgent
from quantmind.llm import GeminiClient
from quantmind.memory import DatabaseManager, VectorStore
from quantmind.scrapers import ScraperOrchestrator
from quantmind.schemas import AgentContext

pytestmark = pytest.mark.live


async def test_memory_accumulates_across_runs():
    db = DatabaseManager()
    await db.init_db()
    vs = VectorStore()
    llm = GeminiClient()
    orch_scraper = ScraperOrchestrator()
    agent = OrchestratorAgent("orchestrator", llm, db, vs)

    # --- RUN 1 ---
    print("=== RUN 1 ===")
    articles = await orch_scraper.scrape_all("NVDA")
    ctx1 = AgentContext(ticker="NVDA", articles=articles)
    result1 = await agent.execute(ctx1)
    assert result1.success is True

    memory1 = result1.data.memory
    print(f"Run 1 memory — days_of_history: {memory1.days_of_history}")
    print(f"Run 1 memory — similar_events: {memory1.similar_past_events}")
    # On the first run, the store is empty for this ticker.
    assert memory1.days_of_history == 0, "First run should have no history"
    assert memory1.similar_past_events == [], "First run should have no vector search results"

    # Wait between runs.
    await asyncio.sleep(3)

    # --- RUN 2 ---
    print("\n=== RUN 2 ===")
    articles2 = await orch_scraper.scrape_all("NVDA")
    ctx2 = AgentContext(ticker="NVDA", articles=articles2)
    result2 = await agent.execute(ctx2)
    assert result2.success is True

    memory2 = result2.data.memory
    print(f"Run 2 memory — days_of_history: {memory2.days_of_history}")
    print(f"Run 2 memory — similar_events count: {len(memory2.similar_past_events)}")
    print(f"Run 2 memory — trend: {memory2.historical_sentiment_trend}")
    # On the second run, both SQLite and ChromaDB hold data from run 1.
    assert memory2.days_of_history >= 1, "Second run must show DB history from run 1"
    assert len(memory2.similar_past_events) > 0, "Second run must retrieve ChromaDB events from run 1"

    # --- DIFF ---
    print("\n=== SYNTHESIS COMPARISON ===")
    print(f"Run 1 synthesis (first 200 chars):\n{result1.data.final_synthesis[:200]}\n")
    print(f"Run 2 synthesis (first 200 chars):\n{result2.data.final_synthesis[:200]}\n")
    print("Memory RAG test PASSED — system learns from prior runs")
