"""StockStalker v2 — Orchestrator Agent (pipeline coordinator).

Not a worker agent: its run() drives the whole pipeline — Memory first
(sequential), then News + Quant in parallel, then one LLM synthesis call, then
persistence. Step D indexes the selected articles into the vector store, which
closes the RAG loop (the next run's Memory Agent retrieves them). Sub-agents are
built from the orchestrator's own injected dependencies.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from stockstalker.agents.base import BaseAgent
from stockstalker.agents.memory_agent import MemoryAgent
from stockstalker.agents.news_agent import NewsAgent
from stockstalker.agents.quant_agent import QuantAgent
from stockstalker.llm.prompts import synthesis_prompt
from stockstalker.schemas import (
    AgentContext,
    AgentResult,
    MemoryContext,
    NewsAnalysis,
    TickerAnalysis,
)
from stockstalker.utils import logger

if TYPE_CHECKING:  # type-only — set at runtime via set_notifiers()
    from stockstalker.integrations.alert_engine import AlertEngine
    from stockstalker.integrations.telegram import StockStalkerBot


class OrchestratorAgent(BaseAgent):
    def __init__(self, name: str, llm, db, vector_store) -> None:
        super().__init__(name, llm, db, vector_store)
        # Optional notifiers, wired by PipelineRunner.enable_telegram().
        self.alert_engine: AlertEngine | None = None
        self.bot: StockStalkerBot | None = None

    def set_notifiers(self, alert_engine: AlertEngine, bot: StockStalkerBot) -> None:
        self.alert_engine = alert_engine
        self.bot = bot

    async def run(self, context: AgentContext) -> AgentResult:
        memory_agent = MemoryAgent("memory_agent", self.llm, self.db, self.vector_store)
        news_agent = NewsAgent("news_agent", self.llm, self.db, self.vector_store)
        quant_agent = QuantAgent("quant_agent", self.llm, self.db, self.vector_store)

        # --- Step A: Memory (sequential, must run first) ---
        logger.info("[{}] Step A: Memory retrieval", self.name)
        memory_result = await memory_agent.execute(context)
        if memory_result.success:
            context.memory = memory_result.data  # subsequent agents see history
        else:
            context.memory = MemoryContext()
            logger.warning(
                "[{}] Memory agent failed — proceeding without history", self.name
            )

        # --- Step B: News + Quant (parallel; both use the updated context) ---
        logger.info("[{}] Step B: News + Quant agents (parallel)", self.name)
        news_result, quant_result = await asyncio.gather(
            news_agent.execute(context),
            quant_agent.execute(context),
            return_exceptions=False,
        )

        try:
            # --- Step C: Synthesis ---
            logger.info("[{}] Step C: Final synthesis", self.name)
            news_analysis = news_result.data if news_result.success else NewsAnalysis()
            quant_analysis = quant_result.data if quant_result.success else None

            ticker_analysis = await self.llm.generate_structured(
                synthesis_prompt(
                    context.ticker, news_analysis, quant_analysis, context.memory
                ),
                TickerAnalysis,
            )
            # The LLM only supplies final_synthesis reliably — force the structured
            # fields to the real objects we already have.
            ticker_analysis.ticker = context.ticker
            ticker_analysis.news = news_analysis
            ticker_analysis.quant = quant_analysis
            ticker_analysis.memory = context.memory
            # Force the real analysis time — the LLM may emit a guessed/past date,
            # which would break the recent-analyses (days=N) retrieval window.
            ticker_analysis.analyzed_at = datetime.now(timezone.utc)

            # --- Step D: Persist (indexing articles closes the RAG loop) ---
            logger.info("[{}] Step D: Persisting results", self.name)
            await self.db.save_analysis(context.ticker, ticker_analysis)
            await self.vector_store.add_articles(news_analysis.selected_articles)
            logger.info(
                "[{}] Indexed {} articles to vector store",
                self.name,
                len(news_analysis.selected_articles),
            )

            # --- Step E: Fire alerts (best-effort; never fails a saved analysis) ---
            if self.alert_engine and self.bot:
                try:
                    alert_messages = await self.alert_engine.evaluate(
                        context.ticker, ticker_analysis
                    )
                    for message in alert_messages:
                        await self.bot.send_message(message)
                        logger.info("[{}] Alert sent for {}", self.name, context.ticker)
                except Exception as exc:  # noqa: BLE001 — alerting must not fail the analysis
                    logger.warning("[{}] alert delivery failed: {}", self.name, exc)

            # --- Step F: Return ---
            return AgentResult(
                agent_name=self.name,
                success=True,
                data=ticker_analysis,
            )
        except Exception as exc:  # noqa: BLE001 — synthesis/persist failures -> failed result
            logger.error(
                "[{}] synthesis/persist error ({}): {}",
                self.name,
                type(exc).__name__,
                exc,
            )
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=str(exc),
                data=None,
            )
