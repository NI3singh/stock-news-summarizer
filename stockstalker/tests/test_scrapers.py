"""StockStalker v2 — scraper layer tests (schema, dedup, isolation, benchmark).

Tests 1 and 4 make REAL network calls (deselected unless run live). Test 3 mocks
the scrapers for a deterministic, fast isolation check.
"""
import time

import pytest

from stockstalker.schemas import Article
from stockstalker.scrapers import (
    FinvizScraper,
    GoogleNewsScraper,
    PolygonScraper,
    ScraperOrchestrator,
    YahooFinanceScraper,
)
from stockstalker.utils import logger


# --- Test 1: Article schema compliance (LIVE) ---
@pytest.mark.parametrize(
    "scraper_cls",
    [PolygonScraper, FinvizScraper, YahooFinanceScraper, GoogleNewsScraper],
)
async def test_article_schema_compliance(scraper_cls):
    async with scraper_cls() as scraper:
        articles = await scraper.scrape("AAPL")

    if not articles:
        logger.warning(
            "{} returned 0 articles (possibly blocked/empty) — skipping per-article asserts",
            scraper_cls.__name__,
        )
        pytest.skip(f"{scraper_cls.__name__} returned no articles")

    for article in articles:
        assert isinstance(article, Article)
        assert len(article.title) > 0
        assert len(article.url) > 0
        assert article.ticker == "AAPL"
        assert 0.0 <= article.credibility_score <= 1.0


# --- Test 2: Deduplication (pure logic) ---
def test_deduplication():
    articles = [
        Article(title=f"Title {i}", url=f"https://e.com/{i}", source="S", ticker="AAPL", content=f"orig {i}")
        for i in range(1, 4)
    ] + [
        # duplicates: same url + title, different content
        Article(title=f"Title {i}", url=f"https://e.com/{i}", source="S", ticker="AAPL", content=f"dup {i}")
        for i in range(1, 4)
    ]
    assert len(articles) == 6
    result = ScraperOrchestrator._deduplicate(articles)
    assert len(result) == 3


# --- Test 3: Exception isolation (mocked for determinism) ---
async def test_exception_isolation(monkeypatch):
    async def _raise(self, ticker):
        raise RuntimeError("polygon boom")

    async def _finviz(self, ticker):
        return [Article(title="Finviz news item", url="https://fv.com/1", source="Finviz (X)", ticker="AAPL")]

    async def _yahoo(self, ticker):
        return [Article(title="Yahoo headline item", url="https://yh.com/1", source="Yahoo Finance", ticker="AAPL")]

    async def _google(self, ticker):
        return [Article(title="Google news item", url="https://gn.com/1", source="Google News (Reuters)", ticker="AAPL")]

    monkeypatch.setattr(PolygonScraper, "scrape", _raise)
    monkeypatch.setattr(FinvizScraper, "scrape", _finviz)
    monkeypatch.setattr(YahooFinanceScraper, "scrape", _yahoo)
    monkeypatch.setattr(GoogleNewsScraper, "scrape", _google)

    result = await ScraperOrchestrator().scrape_all("AAPL")

    # Did NOT raise despite Polygon failing.
    assert isinstance(result, list)
    sources = {a.source for a in result}
    # The other three scrapers still ran and contributed.
    assert any(s.startswith("Finviz") for s in sources)
    assert any(s.startswith("Yahoo") for s in sources)
    assert any(s.startswith("Google") for s in sources)
    # Polygon raised -> contributed nothing.
    assert not any(s.startswith("Polygon") for s in sources)


# --- Test 4: Concurrency benchmark (LIVE) ---
async def test_concurrency_benchmark():
    start = time.monotonic()
    await ScraperOrchestrator().scrape_all("AAPL")
    elapsed = time.monotonic() - start
    print(f"\n[benchmark] scrape_all('AAPL') wall-clock: {elapsed:.1f}s")
    assert elapsed < 15.0
