"""StockStalker v2 — Yahoo Finance RSS scraper.

Fetches the per-ticker headline RSS feed from Yahoo Finance. No API key, no
headless browser — plain httpx + XML parsing. Yahoo occasionally returns an
empty/sparse feed for some tickers; the scraper degrades to [] in that case.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup

from stockstalker.schemas import Article
from stockstalker.scrapers.base import BaseScraper
from stockstalker.utils import logger

_RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"


def _parse_rfc822(raw: str | None) -> datetime | None:
    """Parse an RSS RFC-822 ``pubDate`` to an aware UTC datetime; None on failure."""
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


class YahooFinanceScraper(BaseScraper):
    async def scrape(self, ticker: str) -> list[Article]:
        symbol = ticker.upper()
        params = {"s": symbol, "region": "US", "lang": "en-US"}

        response = await self.async_get(_RSS_URL, params=params)
        if response is None:  # 403/429 -> blocked
            logger.warning("Yahoo Finance: blocked for {}", symbol)
            return []
        if response.status_code != 200:
            logger.warning("Yahoo Finance: HTTP {} for {}", response.status_code, symbol)
            return []

        # XML parser (lxml-xml) is required so <link>/<pubDate> parse correctly.
        soup = BeautifulSoup(response.content, "lxml-xml")
        articles: list[Article] = []
        for item in soup.find_all("item")[:25]:
            title_node = item.find("title")
            link_node = item.find("link")
            title = title_node.get_text(strip=True) if title_node else ""
            url = link_node.get_text(strip=True) if link_node else ""
            if len(title) < 10 or not url:
                continue

            desc_node = item.find("description")
            desc = desc_node.get_text(strip=True) if desc_node else ""
            if "<" in desc:  # strip any embedded HTML the feed put in the snippet
                desc = BeautifulSoup(desc, "lxml").get_text(" ", strip=True)
            pub_node = item.find("pubDate")
            published_at = _parse_rfc822(pub_node.get_text(strip=True) if pub_node else None)

            articles.append(
                Article(
                    title=title,
                    url=url,
                    source="Yahoo Finance",
                    ticker=symbol,
                    published_at=published_at,
                    content=(desc[:500] or title),
                )
            )

        logger.info("Yahoo Finance: found {} articles for {}", len(articles), symbol)
        return articles
