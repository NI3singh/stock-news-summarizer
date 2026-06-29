"""StockStalker v2 — VADER rule-based sentiment + NewsAgent fast-path / fallback.

All offline: VADER runs locally and the NewsAgent tests mock/omit the LLM.
"""
from stockstalker.agents.news_agent import NewsAgent
from stockstalker.agents.vader_sentiment import score_articles, vader_news_analysis
from stockstalker.credibility import credibility_for
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
    assert result.data.composite_sentiment is not None  # scored on every path


# --- Source credibility + composite ---------------------------------------

def test_credibility_tiers():
    assert credibility_for("Polygon (Reuters)") == 1.0
    assert credibility_for("Finviz (Bloomberg)") == 1.0
    assert credibility_for("Google News (CNBC)") == 0.9
    assert credibility_for("Yahoo Finance") == 0.78
    assert credibility_for("Google News (Some Random Blog)") == 0.5  # unknown -> default
    assert credibility_for("") == 0.5


def test_score_articles_per_article_and_weighted_composite():
    arts = _articles([
        ("Apple soars on blockbuster earnings beat and record profit", "great"),
        ("Apple tumbles on weak guidance and lawsuit fears", "bad"),
    ])
    arts[0].source = "Polygon (Reuters)"          # credibility 1.0 (positive article)
    arts[1].source = "Google News (Some Blog)"    # credibility 0.5 (negative article)

    composite = score_articles(arts)
    assert composite is not None and -1.0 <= composite <= 1.0
    for a in arts:
        assert -1.0 <= a.sentiment_score <= 1.0
        assert 0.0 <= a.credibility_score <= 1.0
    assert arts[0].credibility_score == 1.0
    assert arts[1].credibility_score == 0.5
    # the high-credibility positive article pulls the composite above the plain mean
    plain_mean = (arts[0].sentiment_score + arts[1].sentiment_score) / 2
    assert composite > plain_mean


def test_score_articles_empty():
    assert score_articles([]) is None
