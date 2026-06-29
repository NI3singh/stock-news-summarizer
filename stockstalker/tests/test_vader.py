"""StockStalker v2 — VADER rule-based sentiment + NewsAgent fast-path / fallback.

All offline: VADER runs locally and the NewsAgent tests mock/omit the LLM.
"""
from stockstalker.agents.news_agent import NewsAgent
from stockstalker.agents.vader_sentiment import vader_news_analysis
from stockstalker.llm.client import LLMError
from stockstalker.schemas import AgentContext, Article, NewsAnalysis


def _articles(items: list[tuple[str, str]]) -> list[Article]:
    return [
        Article(title=t, url=f"https://e.com/{i}", source="Test", ticker="AAPL", content=c)
        for i, (t, c) in enumerate(items)
    ]


# --- VADER helper ---------------------------------------------------------

def test_vader_directionally_correct():
    pos = vader_news_analysis(
        "AAPL",
        _articles([
            ("Apple soars to record high on blockbuster earnings beat", "strong growth, great results"),
            ("Analysts upgrade Apple, praise surging iPhone demand", "very bullish outlook"),
        ]),
    )
    neg = vader_news_analysis(
        "AAPL",
        _articles([
            ("Apple plunges on disappointing sales and weak guidance", "terrible miss, lawsuit fears"),
            ("Apple faces crushing antitrust probe as shares tumble", "investors fear heavy losses"),
        ]),
    )
    assert -1.0 <= neg.sentiment_score <= 1.0
    assert -1.0 <= pos.sentiment_score <= 1.0
    assert pos.sentiment_score > neg.sentiment_score
    assert pos.selected_articles  # populated
    assert isinstance(pos.key_themes, list)


def test_vader_empty_articles():
    na = vader_news_analysis("AAPL", [])
    assert isinstance(na, NewsAnalysis)
    assert na.sentiment_score == 0.0


# --- NewsAgent integration ------------------------------------------------

async def test_news_agent_vader_fast_path(monkeypatch):
    monkeypatch.setattr(
        "stockstalker.agents.news_agent.settings.sentiment_engine", "vader"
    )
    # llm=None proves the fast path never touches the LLM.
    agent = NewsAgent("news_agent", llm=None, db=None, vector_store=None)
    ctx = AgentContext(
        ticker="AAPL",
        articles=_articles([("Apple rallies on strong quarterly results", "growth")]),
    )
    result = await agent.run(ctx)
    assert result.success
    assert result.data.selected_articles
    assert -1.0 <= result.data.sentiment_score <= 1.0


async def test_news_agent_falls_back_to_vader_on_llm_failure(monkeypatch):
    monkeypatch.setattr(
        "stockstalker.agents.news_agent.settings.sentiment_engine", "llm"
    )

    class _DownLLM:
        async def generate_text(self, *a, **k):
            raise LLMError("gemini unreachable")

        async def generate_structured(self, *a, **k):
            raise LLMError("gemini unreachable")

    agent = NewsAgent("news_agent", llm=_DownLLM(), db=None, vector_store=None)
    ctx = AgentContext(
        ticker="AAPL",
        articles=_articles([
            ("Apple beats earnings, stock jumps", "strong"),
            ("Apple guidance disappoints, shares slip", "weak"),
        ]),
    )
    result = await agent.run(ctx)
    assert result.success  # fell back instead of failing the agent
    assert result.data.selected_articles
    assert -1.0 <= result.data.sentiment_score <= 1.0
