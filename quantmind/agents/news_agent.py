"""QuantMind v2 — News Intelligence Agent.

Two LLM steps: (1) select the most valuable articles (generate_text → JSON index
array), then (2) produce a structured NewsAnalysis (generate_structured). LLM
failures propagate to BaseAgent.execute(), which records them as a failed result.
"""
import json
import time

from quantmind.agents.base import BaseAgent
from quantmind.llm.prompts import news_analyze_prompt, news_select_prompt
from quantmind.schemas import AgentContext, AgentResult, NewsAnalysis
from quantmind.utils import logger


class NewsAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        if not context.articles:
            return AgentResult(
                agent_name=self.name,
                success=False,
                error="No articles available for analysis",
                data=None,
            )

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

        return AgentResult(
            agent_name=self.name,
            success=True,
            data=news_analysis,
        )
