"""StockStalker v2 — Memory Agent.

The only agent that never calls the LLM — pure data retrieval. It fetches
semantically-similar past events from the vector store and recent analyses from
SQL (concurrently) and assembles a MemoryContext that flows into every later agent.
"""
import asyncio

from stockstalker.agents.base import BaseAgent
from stockstalker.schemas import AgentContext, AgentResult, MemoryContext
from stockstalker.utils import logger


class MemoryAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        logger.info("[{}] Fetching history for {}", self.name, context.ticker)

        # Vector search and recent analyses (SQL) run concurrently.
        similar_events, recent_analyses = await asyncio.gather(
            self.vector_store.search_similar(
                query=f"{context.ticker} stock news analysis financial",
                ticker=context.ticker,
                n=5,
            ),
            self.db.get_recent_analyses(context.user_id, context.ticker, days=7),
        )

        if not recent_analyses:
            historical_sentiment_trend = "No prior analysis available"
        else:
            # Average the most recent up-to-3 sentiment scores (skip NULLs).
            scores = [
                a.get("sentiment_score")
                for a in recent_analyses[:3]
                if a.get("sentiment_score") is not None
            ]
            avg = sum(scores) / len(scores) if scores else 0.0
            n = len(recent_analyses)
            if avg > 0.3:
                historical_sentiment_trend = f"Trending positive over last {n} days"
            elif avg < -0.3:
                historical_sentiment_trend = f"Trending negative over last {n} days"
            else:
                historical_sentiment_trend = f"Neutral trend over last {n} days"

        memory_context = MemoryContext(
            similar_past_events=similar_events,
            historical_sentiment_trend=historical_sentiment_trend,
            days_of_history=len(recent_analyses),
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data=memory_context,
        )
