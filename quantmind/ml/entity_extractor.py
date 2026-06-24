"""QuantMind ML — LLM entity / relationship extraction (Phase D.5).

Uses the LLM (structured output) to pull companies, people, products, events, and
regulatory bodies — plus the FACTUAL relationships between them — out of a ticker's
news. The post-processing stamps each entity with the source ticker and best-effort
article attribution. Failures degrade to an empty result (never raise).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from quantmind.llm import LLMStructuredOutputError
from quantmind.llm.prompts import entity_extraction_prompt
from quantmind.schemas import EntityExtractionResult
from quantmind.utils import logger

if TYPE_CHECKING:
    from quantmind.llm import GeminiClient
    from quantmind.schemas import Article


class EntityExtractor:
    """Extracts entities + relationships from a ticker's articles via the LLM."""

    def __init__(self, llm: GeminiClient) -> None:
        self.llm = llm

    async def extract(self, ticker: str, articles: list[Article]) -> EntityExtractionResult:
        ticker = ticker.upper().strip()
        if not articles:
            return EntityExtractionResult()

        prompt = entity_extraction_prompt(ticker, articles)
        try:
            result = await self.llm.generate_structured(prompt, EntityExtractionResult)
        except LLMStructuredOutputError as exc:
            logger.warning("Entity extraction failed for {}: {}", ticker, exc)
            return EntityExtractionResult()

        # Stamp the source ticker (meta — not produced by the LLM).
        for entity in result.entities:
            entity.ticker = ticker

        # Best-effort article attribution (keep any URL the LLM already set).
        for rel in result.relationships:
            rel.mentioned_in_article = next(
                (
                    a.url
                    for a in articles
                    if a.title in rel.source_entity or a.title in rel.target_entity
                ),
                rel.mentioned_in_article or "",
            )

        logger.info(
            "Extracted {} entities, {} relationships for {}",
            len(result.entities),
            len(result.relationships),
            ticker,
        )
        return result
