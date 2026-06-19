"""QuantMind v2 — TradingView news scraper (crawl4ai / Playwright).

TradingView renders news with JavaScript, so this scraper uses crawl4ai's
``AsyncWebCrawler`` (its own headless browser) rather than the base httpx client.
To keep latency low it launches ONE browser and crawls all candidate exchange
URLs concurrently (``arun_many``), then returns the highest-priority exchange that
yielded articles. crawl4ai is imported lazily and any failure degrades to [].
"""
import json
from datetime import datetime

from quantmind.schemas import Article
from quantmind.scrapers.base import BaseScraper
from quantmind.utils import logger

_EXCHANGES = ["NASDAQ", "NYSE", "NSE"]

_SCHEMA = {
    "name": "TradingView News",
    "baseSelector": "article",
    "fields": [
        {"name": "title", "selector": "a", "type": "text"},
        {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
        {"name": "time", "selector": "time", "type": "attribute", "attribute": "datetime"},
        {"name": "snippet", "selector": "p", "type": "text"},
    ],
}


class TradingViewScraper(BaseScraper):
    def _extract_articles(self, extracted_content: str, symbol: str) -> list[Article]:
        """Map crawl4ai's extracted JSON to Article objects."""
        articles: list[Article] = []
        for item in json.loads(extracted_content):
            title = item.get("title", "").strip()
            if len(title) <= 15:
                continue
            article_url = item.get("url", "")
            if not article_url.strip():
                continue
            if not article_url.startswith("http"):
                article_url = "https://www.tradingview.com" + article_url

            published_at = None
            raw_time = item.get("time")
            if raw_time:
                try:
                    published_at = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    published_at = None

            articles.append(
                Article(
                    title=title,
                    url=article_url,
                    source="TradingView",
                    ticker=symbol,
                    published_at=published_at,
                    content=item.get("snippet", "") or title,
                )
            )
        return articles

    async def scrape(self, ticker: str) -> list[Article]:
        # Lazy import — keeps crawl4ai/Playwright off the module-import path, and
        # guarantees we degrade to [] (never crash) if crawl4ai isn't available.
        try:
            from crawl4ai import (
                AsyncWebCrawler,
                BrowserConfig,
                CacheMode,
                CrawlerRunConfig,
            )
            from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
        except ImportError as exc:
            logger.warning("crawl4ai not available: {}", exc)
            return []

        symbol = ticker.upper()
        urls = [
            f"https://www.tradingview.com/symbols/{exchange}-{symbol}/news/"
            for exchange in _EXCHANGES
        ]
        run_config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(_SCHEMA),
            cache_mode=CacheMode.BYPASS,
        )

        # One browser; crawl all exchanges concurrently to keep wall-clock low.
        try:
            async with AsyncWebCrawler(
                config=BrowserConfig(headless=True, verbose=False)
            ) as crawler:
                results = await crawler.arun_many(urls=urls, config=run_config)
        except Exception as exc:  # noqa: BLE001 — degrade to [] on any crawl/browser error
            logger.warning("TradingView crawl failed for {}: {}", symbol, exc)
            return []

        # Map each result to its exchange; keep the highest-priority non-empty one.
        by_exchange: dict[str, list[Article]] = {}
        for result in results:
            content = getattr(result, "extracted_content", None)
            if not content:
                continue
            try:
                parsed = self._extract_articles(content, symbol)
            except Exception as exc:  # noqa: BLE001
                logger.warning("TradingView parse error: {}", exc)
                continue
            if not parsed:
                continue
            result_url = getattr(result, "url", "") or ""
            for exchange in _EXCHANGES:
                if f"{exchange}-{symbol}" in result_url:
                    by_exchange[exchange] = parsed
                    break

        for exchange in _EXCHANGES:
            if by_exchange.get(exchange):
                logger.info(
                    "TradingView: found {} articles for {} via {}",
                    len(by_exchange[exchange]),
                    symbol,
                    exchange,
                )
                return by_exchange[exchange][:20]

        logger.warning("TradingView: no articles for {}", symbol)
        return []
