"""StockStalker v2 — News Intelligence Agent.

Default path: two LLM steps — (1) select the most valuable articles, then (2)
produce a structured NewsAnalysis. If the LLM is unreachable, or if
``settings.sentiment_engine == "vader"``, a rule-based VADER analysis is used
instead — so the pipeline always yields a sentiment score.
"""
import json
import time

from stockstalker.agents.base import BaseAgent
from stockstalker.agents.vader_sentiment import vader_news_analysis
from stockstalker.config import settings
from stockstalker.llm.client import LLMError
from stockstalker.llm.prompts import news_analyze_prompt, news_select_prompt
from stockstalker.schemas import AgentContext, AgentResult, NewsAnalysis
from stockstalker.utils import logger


class NewsAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        if not context.articles:
            return AgentResult(
                agent_name=self.name,
                success=False,
                error="No articles available for analysis",
                data=None,
            )

        # Fast path: rule-based engine explicitly selected — skip the LLM entirely.
        if settings.sentiment_engine.lower() == "vader":
            logger.info("[{}] sentiment_engine=vader — using rule-based path", self.name)
            return AgentResult(
                agent_name=self.name,
                success=True,
                data=vader_news_analysis(context.ticker, context.articles),
            )

        # Default: LLM path, with an automatic VADER fallback if Gemini is unreachable.
        try:
            news_analysis = await self._analyze_with_llm(context)
        except LLMError as exc:
            logger.warning(
                "[{}] LLM unavailable ({}) — falling back to VADER", self.name, exc
            )
            return AgentResult(
                agent_name=self.name,
                success=True,
                data=vader_news_analysis(context.ticker, context.articles),
            )

        return AgentResult(agent_name=self.name, success=True, data=news_analysis)

    async def _analyze_with_llm(self, context: AgentContext) -> NewsAnalysis:
        """Two-step LLM analysis. Raises LLMError if the model is unreachable."""
        # --- Step 1: article selection (free text → JSON index array) ---
        t1 = time.time()
        raw_selection = await self.llm.generate_text(
            news_select_prompt(context.ticker, context.articles)
        )
        logger.info("[{}] Selection LLM call: {:.2f}s", self.name, time.time() - t1)

        raw = raw_selection.strip()
        try:
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start == -1 or end == 0:
                raise ValueError("no JSON array found")
            indices = json.loads(raw[start:end])
            if not isinstance(indices, list):
                raise ValueError("selection is not a list")
        except (ValueError, json.JSONDecodeError):
            logger.warning(
                "[{}] Could not parse selection, using first 7 articles", self.name
            )
            indices = [1, 2, 3, 4, 5, 6, 7]

        valid_indices = [
            i for i in indices if isinstance(i, int) and 1 <= i <= len(context.articles)
        ]
        if not valid_indices:  # all out of range -> fall back to the first few
            valid_indices = list(range(1, min(7, len(context.articles)) + 1))
        selected = [context.articles[i - 1] for i in valid_indices]

        # --- Step 2: structured news analysis ---
        t2 = time.time()
        news_analysis = await self.llm.generate_structured(
            news_analyze_prompt(context.ticker, selected, context.memory),
            NewsAnalysis,
        )
        logger.info("[{}] Analysis LLM call: {:.2f}s", self.name, time.time() - t2)

        # Attach the real selected articles if the LLM left the field empty.
        if not news_analysis.selected_articles:
            news_analysis.selected_articles = selected
        return news_analysis
