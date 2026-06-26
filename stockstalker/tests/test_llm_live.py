"""StockStalker v2 — live LLM integration test (hits the real Gemini API).

Marked ``live`` and DESELECTED by default (pyproject ``addopts = -m 'not live'``).
Run explicitly:  pytest stockstalker/tests/test_llm_live.py -v -m live -s
Requires a real GEMINI_API_KEY in .env.
"""
import json

import pytest

from stockstalker.llm import GeminiClient, news_analyze_prompt, news_select_prompt
from stockstalker.schemas import Article, MemoryContext, NewsAnalysis

pytestmark = pytest.mark.live

_ARTICLES = [
    Article(
        title="Apple Reports Record Q4 Revenue, Beating Analyst Estimates",
        url="https://example.com/aapl-earnings",
        source="Reuters",
        ticker="AAPL",
        content="Apple posted record quarterly revenue of $95 billion, topping Wall Street "
        "estimates on strong iPhone demand and double-digit Services growth.",
    ),
    Article(
        title="Apple Unveils iPhone 17 With On-Device AI Features",
        url="https://example.com/aapl-iphone",
        source="The Verge",
        ticker="AAPL",
        content="At its fall event Apple introduced the iPhone 17, featuring a faster neural "
        "engine and new on-device generative AI capabilities.",
    ),
    Article(
        title="Morgan Stanley Raises Apple Price Target to $300 on Services Growth",
        url="https://example.com/aapl-rating",
        source="CNBC",
        ticker="AAPL",
        content="Morgan Stanley lifted its Apple price target to $300, citing accelerating "
        "Services revenue and resilient hardware margins.",
    ),
    Article(
        title="Apple Faces EU Antitrust Lawsuit Over App Store Practices",
        url="https://example.com/aapl-lawsuit",
        source="Bloomberg",
        ticker="AAPL",
        content="European regulators filed an antitrust complaint alleging Apple's App Store "
        "fees and rules harm competition among app developers.",
    ),
    Article(
        title="Apple Shares Rise 3% as Broad Tech Rally Lifts Indices",
        url="https://example.com/aapl-market",
        source="MarketWatch",
        ticker="AAPL",
        content="Apple stock climbed 3% amid a broad technology rally that pushed major "
        "indices higher on easing interest-rate concerns.",
    ),
]


async def test_full_llm_pipeline():
    client = GeminiClient()

    # Step 1 — generate_text
    response = await client.generate_text("Respond with exactly the word: STOCKSTALKER_OK")
    assert "STOCKSTALKER_OK" in response.upper()

    # Step 2 — news selection (generate_text returning a JSON array)
    raw = (await client.generate_text(news_select_prompt("AAPL", _ARTICLES))).strip()
    if raw.startswith("```"):  # tolerate ```json fences
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1]).strip() if len(lines) >= 3 else raw.strip("`")
    parsed = json.loads(raw)
    assert isinstance(parsed, list)
    assert all(isinstance(i, int) and 1 <= i <= 5 for i in parsed)
    assert 3 <= len(parsed) <= 7

    # Step 3 — structured output
    selected = [_ARTICLES[i - 1] for i in parsed[:3]]
    memory = MemoryContext(days_of_history=0)
    news_analysis = await client.generate_structured(
        news_analyze_prompt("AAPL", selected, memory), NewsAnalysis
    )
    assert isinstance(news_analysis, NewsAnalysis)
    assert -1.0 <= news_analysis.sentiment_score <= 1.0
    assert len(news_analysis.summary) > 100
    assert len(news_analysis.key_themes) >= 2

    # Step 4 — print results
    print("\nsentiment_score:", news_analysis.sentiment_score)
    print("key_themes:", news_analysis.key_themes)
    print("summary[:200]:", news_analysis.summary[:200])
    print("LLM integration test PASSED")
