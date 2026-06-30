"""StockStalker v2 — Pipeline Runner (shared-resource orchestration entry point).

The single long-lived object that owns every shared resource — the database,
vector store, LLM client, scraper orchestrator, and the agent orchestrator — and
reuses them for every ticker. Resources are built ONCE in ``__init__`` (never
per call), so a long-running scheduler or a batch run pays the heavy setup cost
(vector store, LangChain model, etc.) exactly once.

The five heavy resource imports are deferred into ``__init__`` so that merely
importing this module (e.g. for the CLI's argparse wiring) stays cheap —
langchain and the scraper stack only load when a runner is actually constructed.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from stockstalker.config import settings
from stockstalker.schemas import AgentContext, TickerAnalysis
from stockstalker.utils import logger

if TYPE_CHECKING:  # type-only — instantiated lazily in enable_telegram()
    from stockstalker.integrations.alert_engine import AlertEngine
    from stockstalker.integrations.telegram import StockStalkerBot


class PipelineRunner:
    """Owns all shared resources and runs single/batch ticker analyses."""

    def __init__(self) -> None:
        # Deferred (heavy) imports — keep `import stockstalker.pipeline` lightweight.
        from stockstalker.agents import OrchestratorAgent
        from stockstalker.llm import GeminiClient
        from stockstalker.memory import DatabaseManager, VectorStore
        from stockstalker.scrapers import ScraperOrchestrator

        # Built ONCE — reused for every analyze_ticker / analyze_all call.
        self.db = DatabaseManager()
        self.vector_store = VectorStore()
        self.llm = GeminiClient()
        self.scraper = ScraperOrchestrator()
        self.orchestrator = OrchestratorAgent(
            "orchestrator", self.llm, self.db, self.vector_store
        )
        self._initialized = False

        # Optional Telegram integration (wired by enable_telegram()).
        self.alert_engine: AlertEngine | None = None
        self.bot: StockStalkerBot | None = None

    async def initialize(self) -> None:
        """Create the DB tables once. Idempotent — safe to call repeatedly."""
        if not self._initialized:
            await self.db.init_db()
            await self.vector_store.ensure_schema()
            self._initialized = True
            logger.info("PipelineRunner initialized")

    def enable_telegram(self) -> None:
        """Wire up the Telegram bot + alert engine (no-op if creds are unset)."""
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.warning(
                "Telegram credentials not set — skipping bot initialization"
            )
            return
        from stockstalker.integrations.alert_engine import AlertEngine
        from stockstalker.integrations.telegram import StockStalkerBot

        self.bot = StockStalkerBot(self)
        self.alert_engine = AlertEngine(self.db)
        self.orchestrator.set_notifiers(self.alert_engine, self.bot)
        logger.info("Telegram bot enabled")

    async def analyze_ticker(self, user_id: str, ticker: str) -> TickerAnalysis:
        """Scrape + run the full agent pipeline for one user's ticker."""
        await self.initialize()
        ticker = ticker.upper().strip()
        logger.info("Analyzing {} for {}...", ticker, user_id)

        articles = await self.scraper.scrape_all(ticker)
        ctx = AgentContext(ticker=ticker, user_id=user_id, articles=articles)
        result = await self.orchestrator.execute(ctx)

        if not result.success:
            raise RuntimeError(f"Analysis failed for {ticker}: {result.error}")

        return result.data

    async def analyze_all(self, pairs: list[tuple[str, str]]) -> list[TickerAnalysis]:
        """Analyze many (user_id, ticker) pairs concurrently, capped by
        max_concurrent_tickers. One failure logs + yields ``None`` (filtered out)
        rather than aborting the whole batch.
        """
        await self.initialize()

        sem = asyncio.Semaphore(settings.max_concurrent_tickers)

        async def analyze_with_sem(user_id: str, ticker: str) -> TickerAnalysis | None:
            async with sem:
                try:
                    return await self.analyze_ticker(user_id, ticker)
                except Exception as exc:  # noqa: BLE001 — one ticker must not abort the batch
                    logger.error("Failed to analyze {}: {}", ticker, exc)
                    return None

        tasks = [analyze_with_sem(uid, t) for uid, t in pairs]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        successful = [r for r in results if r is not None]
        logger.info("analyze_all complete: {}/{} succeeded", len(successful), len(pairs))
        return successful
