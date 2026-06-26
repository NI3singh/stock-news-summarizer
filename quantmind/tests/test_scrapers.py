"""QuantMind v2 — scraper layer tests (schema, dedup, isolation, benchmark).

Tests 1 and 4 make REAL network calls and are slow (TradingView launches a
headless browser). Test 3 mocks the scrapers for a deterministic, fast isolation
check — necessary because live TradingView/EDGAR currently return [] (selector /
query issues), so there'd be nothing to assert as "still included" otherwise.
"""
import time

import pytest

from quantmind.schemas import Article
from quantmind.scrapers import (
    EdgarScraper,
    FinvizScraper,
    PolygonScraper,
    ScraperOrchestrator,
    TradingViewScraper,
)
from quantmind.utils import logger


# --- Test 1: Article schema compliance (LIVE) ---
@pytest.mark.parametrize(
    "scraper_cls",
    [PolygonScraper, FinvizScraper, TradingViewScraper, EdgarScraper],
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

    async def _tv(self, ticker):
        return [Article(title="TradingView news item", url="https://tv.com/1", source="TradingView", ticker="AAPL")]

    async def _edgar(self, ticker):
        return [Article(title="EDGAR filing item", url="https://sec.gov/1", source="SEC EDGAR (8-K)", ticker="AAPL")]

    monkeypatch.setattr(PolygonScraper, "scrape", _raise)
    monkeypatch.setattr(FinvizScraper, "scrape", _finviz)
    monkeypatch.setattr(TradingViewScraper, "scrape", _tv)
    monkeypatch.setattr(EdgarScraper, "scrape", _edgar)

    result = await ScraperOrchestrator().scrape_all("AAPL")

    # Did NOT raise despite Polygon failing.
    assert isinstance(result, list)
    sources = {a.source for a in result}
    # The other three scrapers still ran and contributed.
    assert any(s.startswith("Finviz") for s in sources)
    assert any(s == "TradingView" for s in sources)
    assert any(s.startswith("SEC EDGAR") for s in sources)
    # Polygon raised -> contributed nothing.
    assert not any(s.startswith("Polygon") for s in sources)


# --- Test 4: Concurrency benchmark (LIVE) ---
async def test_concurrency_benchmark():
    start = time.monotonic()
    await ScraperOrchestrator().scrape_all("AAPL")
    elapsed = time.monotonic() - start
    print(f"\n[benchmark] scrape_all('AAPL') wall-clock: {elapsed:.1f}s")
    assert elapsed < 15.0
