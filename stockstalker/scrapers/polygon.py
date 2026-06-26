"""StockStalker v2 — Polygon.io news scraper (REST API).

Fetches the last 7 days of news for a ticker from Polygon's
``/v2/reference/news`` endpoint and maps results to ``Article`` objects.
"""
from datetime import datetime, timedelta, timezone

from stockstalker.config import settings
from stockstalker.schemas import Article
from stockstalker.scrapers.base import BaseScraper
from stockstalker.utils import logger

_NEWS_URL = "https://api.polygon.io/v2/reference/news"


class PolygonScraper(BaseScraper):
    async def scrape(self, ticker: str) -> list[Article]:
        symbol = ticker.upper()
        now = datetime.now(timezone.utc)
        params = {
            "ticker": symbol,
            "order": "desc",
            "limit": 20,
            "apiKey": settings.polygon_api_key,
            "published_utc.gte": (now - timedelta(days=7)).strftime("%Y-%m-%d"),
            "published_utc.lte": now.strftime("%Y-%m-%d"),
        }

        response = await self.async_get(_NEWS_URL, params=params)
        if response is None:  # 403/429 -> blocked
            logger.warning("Polygon: blocked (403/429) for {}", symbol)
            return []

        if response.status_code != 200:
            logger.warning("Polygon: HTTP {} for {}", response.status_code, symbol)
            return []

        data = response.json()
        if data.get("status") != "OK":
            logger.warning("Polygon: status={} for {}", data.get("status"), symbol)
            return []

        articles: list[Article] = []
        for item in data.get("results", []):
            title = item.get("title", "").strip()
            url = item.get("article_url", "")
            if not title or not url.strip():
                continue

            published_at = None
            raw = item.get("published_utc")
            if raw:
                try:
                    published_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    published_at = None

            publisher_name = item.get("publisher", {}).get("name", "Unknown")
            articles.append(
                Article(
                    title=title,
                    url=url,
                    source=f"Polygon ({publisher_name})",
                    ticker=symbol,
                    published_at=published_at,
                    content=item.get("description", "") or item.get("title", ""),
                )
            )

        logger.info("Polygon: found {} articles for {}", len(articles), symbol)
        return articles
