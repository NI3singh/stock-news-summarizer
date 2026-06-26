"""StockStalker v2 — SEC EDGAR full-text search scraper (REST API).

EDGAR is a pure JSON REST API (no HTML scraping / JS). SEC REQUIRES a descriptive
User-Agent identifying the application + contact — a generic or missing UA gets the
IP blocked — so this scraper overrides ``get_headers()`` with a fixed SEC-compliant
UA (no fake-useragent).
"""
from datetime import datetime, timedelta, timezone

from stockstalker.schemas import Article
from stockstalker.scrapers.base import BaseScraper
from stockstalker.utils import logger

_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
_SEC_USER_AGENT = "StockStalker-Research-Bot contact@example.com"


class EdgarScraper(BaseScraper):
    def get_headers(self) -> dict:
        # SEC requires a descriptive UA; do NOT use fake-useragent here.
        return {
            "User-Agent": _SEC_USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }

    async def scrape(self, ticker: str) -> list[Article]:
        symbol = ticker.upper()
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=14)
        params = {
            "q": f'"{symbol}"',
            "dateRange": "custom",
            "startdt": start.strftime("%Y-%m-%d"),
            "enddt": end.strftime("%Y-%m-%d"),
            "forms": "8-K",
        }

        response = await self.async_get(_SEARCH_URL, params=params)
        if response is None or response.status_code != 200:
            status = response.status_code if response is not None else "blocked"
            logger.warning("EDGAR: no data for {} (status {})", symbol, status)
            return []

        hits = response.json().get("hits", {}).get("hits", [])
        articles: list[Article] = []
        for hit in hits[:10]:
            source_data = hit.get("_source", {})
            file_date = source_data.get("file_date", "")
            form_type = source_data.get("form_type", "8-K")
            entity_name = source_data.get("entity_name", symbol)
            period = source_data.get("period_of_report", "")
            filing_url = (
                "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
                f"&CIK={source_data.get('entity_id', '')}"
                "&type=8-K&dateb=&owner=include&count=10"
            )

            published_at = None
            if file_date:
                try:
                    published_at = datetime.strptime(file_date, "%Y-%m-%d")
                except (ValueError, TypeError):
                    published_at = None

            articles.append(
                Article(
                    title=f"{entity_name} — {form_type} Filing ({period or file_date})",
                    url=filing_url,
                    source=f"SEC EDGAR ({form_type})",
                    ticker=symbol,
                    published_at=published_at,
                    content=f"{form_type} filing by {entity_name} for period {period}",
                )
            )

        logger.info("EDGAR: found {} filings for {}", len(articles), symbol)
        return articles
