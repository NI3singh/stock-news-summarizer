"""QuantMind v2 — Finviz quote-page news scraper (HTML).

Scrapes the news table on a ticker's Finviz quote page. Finviz frequently returns
403 from datacenter IPs; the scraper degrades to [] rather than crashing.
"""
from bs4 import BeautifulSoup

from quantmind.schemas import Article
from quantmind.scrapers.base import BaseScraper
from quantmind.utils import logger


class FinvizScraper(BaseScraper):
    async def scrape(self, ticker: str) -> list[Article]:
        symbol = ticker.upper()
        url = f"https://finviz.com/quote.ashx?t={symbol}"

        response = await self.async_get(url)
        if response is None:  # 403/429 -> blocked
            logger.warning("Finviz blocked request for {}", symbol)
            return []

        soup = BeautifulSoup(response.content, "lxml")
        news_table = soup.find("table", {"id": "news-table"})
        if not news_table:
            logger.warning("Finviz: no news-table found for {}", symbol)
            return []

        articles: list[Article] = []
        current_date = None
        for row in news_table.find_all("tr")[:25]:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            # Ported date tracking: a first cell with date+time (>8 chars) starts a
            # new date; a time-only cell belongs to current_date. The combined value
            # is intentionally NOT stored (published_at=None below) — Finviz's
            # "Mon-DD-YY" format isn't a reliable datetime — kept for parity/future use.
            date_cell = cols[0].get_text(strip=True)
            if len(date_cell) > 8:
                current_date = date_cell
            elif current_date:
                date_cell = f"{current_date.split()[0]} {date_cell}"

            anchor = cols[1].find("a")
            if not anchor:
                continue
            title = anchor.get_text(strip=True)
            article_url = anchor.get("href", "")
            if len(title) < 10 or not article_url.strip():
                continue

            source_span = row.find("span")
            # Finviz already wraps the publisher in parens (e.g. "(Bloomberg)"),
            # so strip them to avoid a doubled "Finviz ((Bloomberg))".
            source = source_span.get_text(strip=True).strip("()") if source_span else "Finviz"

            articles.append(
                Article(
                    title=title,
                    url=article_url,
                    source=f"Finviz ({source})",
                    ticker=symbol,
                    published_at=None,
                    content=title,
                )
            )

        logger.info("Finviz: found {} articles for {}", len(articles), symbol)
        return articles
