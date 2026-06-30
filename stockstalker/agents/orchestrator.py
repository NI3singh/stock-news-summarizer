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
from stockstalker.config import settings
from stockstalker.llm.client import LLMError
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


def _fallback_synthesis(ticker: str, news: NewsAnalysis, quant) -> str:
    """Build a final_synthesis without the LLM (used when the model is unreachable)."""
    parts = [f"{ticker}: rule-based summary (AI model unavailable)."]
    if news.summary:
        parts.append(news.summary)
    if quant is not None and quant.signals is not None:
        s = quant.signals
        bits = []
        if s.rsi is not None:
            bits.append(f"RSI {s.rsi}")
        if s.macd is not None:
            bits.append(f"MACD {s.macd}")
        if s.volume_ratio is not None:
            bits.append(f"Vol {s.volume_ratio}x")
        if s.price_change_pct is not None:
            bits.append(f"Change {s.price_change_pct}%")
        if bits:
            parts.append("Signals: " + ", ".join(bits) + ".")
    return " ".join(parts).strip()


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

            try:
                ticker_analysis = await self.llm.generate_structured(
                    synthesis_prompt(
                        context.ticker, news_analysis, quant_analysis, context.memory
                    ),
                    TickerAnalysis,
                )
            except LLMError as exc:
                # LLM unreachable — build a degraded report so the run still produces
                # (and persists) a usable analysis from the VADER news + signals.
                logger.warning(
                    "[{}] Synthesis LLM unavailable ({}) — using a rule-based summary",
                    self.name,
                    exc,
                )
                ticker_analysis = TickerAnalysis(
                    ticker=context.ticker,
                    news=news_analysis,
                    memory=context.memory,
                    final_synthesis=_fallback_synthesis(
                        context.ticker, news_analysis, quant_analysis
                    ),
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
            await self.db.save_analysis(context.user_id, context.ticker, ticker_analysis)
            # Vector indexing is best-effort: embeddings need the LLM provider, so a
            # provider outage must not fail an already-saved analysis.
            try:
                await self.vector_store.add_articles(news_analysis.selected_articles)
                logger.info(
                    "[{}] Indexed {} articles to vector store",
                    self.name,
                    len(news_analysis.selected_articles),
                )
            except Exception as exc:  # noqa: BLE001 — indexing must not fail the run
                logger.warning(
                    "[{}] Vector indexing skipped (embeddings unavailable): {}",
                    self.name,
                    exc,
                )

            # --- Step E: Fire alerts (best-effort; never fails a saved analysis) ---
            # Rules + events are per-user. Telegram delivery only happens for the
            # OWNER's analyses (the deployer linked to TELEGRAM_CHAT_ID); other users'
            # alerts are still recorded as events, visible in their web Alerts page.
            if self.alert_engine:
                try:
                    alert_messages = await self.alert_engine.evaluate(
                        context.user_id, context.ticker, ticker_analysis
                    )
                    if self.bot and context.user_id == settings.effective_owner_uid:
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
