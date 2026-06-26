"""StockStalker v2 scrapers — concurrent multi-source orchestrator.

Runs all source scrapers concurrently (each isolated so one failure can't abort
the others), flattens, and deduplicates by URL+title.
"""
import asyncio
import hashlib
import time

from stockstalker.schemas import Article
from stockstalker.scrapers.finviz import FinvizScraper
from stockstalker.scrapers.polygon import PolygonScraper
from stockstalker.scrapers.sec_edgar import EdgarScraper
from stockstalker.scrapers.tradingview import TradingViewScraper
from stockstalker.utils import logger

__all__ = [
    "ScraperOrchestrator",
    "PolygonScraper",
    "FinvizScraper",
    "TradingViewScraper",
    "EdgarScraper",
]


class ScraperOrchestrator:
    """Runs all source scrapers concurrently and returns deduplicated articles."""

    def __init__(self) -> None:
        # No shared state — each scraper is instantiated per-call as an async CM.
        pass

    @staticmethod
    def _deduplicate(articles: list[Article]) -> list[Article]:
        """Drop duplicate articles by URL+title, keeping the first occurrence."""
        seen: set[str] = set()
        unique: list[Article] = []
        for article in articles:
            key = hashlib.md5(
                (article.url.strip().lower() + article.title.strip().lower()).encode()
            ).hexdigest()
            if key not in seen:
                seen.add(key)
                unique.append(article)
        return unique

    async def scrape_all(self, ticker: str) -> list[Article]:
        symbol = ticker.upper()
        logger.info("Starting concurrent scrape for {}", symbol)
        start = time.monotonic()

        async def _run(scraper_cls, name: str, timeout: float) -> list[Article]:
            """Isolated scraper task — never raises; [] on any failure or timeout.

            A per-source timeout keeps one slow source (notably the browser-based
            TradingView crawl, ~25-30s) from blowing the pipeline's latency budget.
            """
            try:
                async with scraper_cls() as scraper:
                    return await asyncio.wait_for(scraper.scrape(symbol), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("{} scraper timed out after {:.0f}s", name, timeout)
                return []
            except Exception as exc:  # noqa: BLE001 — one source must not abort the rest
                logger.warning("{} scraper failed: {}", name, exc)
                return []

        results = await asyncio.gather(
            _run(PolygonScraper, "Polygon", 20.0),
            _run(FinvizScraper, "Finviz", 20.0),
            _run(TradingViewScraper, "TradingView", 10.0),
            _run(EdgarScraper, "EDGAR", 20.0),
            return_exceptions=False,
        )

        all_articles = [article for sublist in results for article in sublist]
        logger.info(
            "Polygon: {} | Finviz: {} | TradingView: {} | EDGAR: {} | Total raw: {}",
            len(results[0]),
            len(results[1]),
            len(results[2]),
            len(results[3]),
            len(all_articles),
        )

        unique = self._deduplicate(all_articles)

        elapsed = time.monotonic() - start
        logger.info(
            "Scrape complete for {} in {:.1f}s — {} unique ({} dupes removed)",
            symbol,
            elapsed,
            len(unique),
            len(all_articles) - len(unique),
        )
        return unique
