"""StockStalker v2 — Google News RSS scraper.

Queries Google News' free RSS search feed for recent articles about a ticker.
No API key, no headless browser — plain httpx + XML parsing. Degrades to [] on
any block/parse failure.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup

from stockstalker.schemas import Article
from stockstalker.scrapers.base import BaseScraper
from stockstalker.utils import logger

_RSS_URL = "https://news.google.com/rss/search"


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


class GoogleNewsScraper(BaseScraper):
    async def scrape(self, ticker: str) -> list[Article]:
        symbol = ticker.upper()
        params = {
            "q": f"{symbol} stock when:7d",
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }

        response = await self.async_get(_RSS_URL, params=params)
        if response is None:  # 403/429 -> blocked
            logger.warning("Google News: blocked for {}", symbol)
            return []
        if response.status_code != 200:
            logger.warning("Google News: HTTP {} for {}", response.status_code, symbol)
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

            src_node = item.find("source")
            publisher = src_node.get_text(strip=True) if src_node else "Google News"
            pub_node = item.find("pubDate")
            published_at = _parse_rfc822(pub_node.get_text(strip=True) if pub_node else None)

            articles.append(
                Article(
                    title=title,
                    url=url,
                    source=f"Google News ({publisher})",
                    ticker=symbol,
                    published_at=published_at,
                    # Google News descriptions are HTML link-lists, not prose — use
                    # the headline as the content to embed/analyze.
                    content=title,
                )
            )

        logger.info("Google News: found {} articles for {}", len(articles), symbol)
        return articles
