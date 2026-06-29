"""StockStalker v2 — rule-based (VADER) news sentiment.

A cheap, network-free sentiment path the NewsAgent uses two ways:
  • Fast path — when ``settings.sentiment_engine == "vader"`` (skip the LLM).
  • Fallback  — when the LLM is unreachable, so analysis still yields a score.

VADER's ``compound`` score is already in [-1, +1], matching NewsAnalysis.sentiment_score.
The vaderSentiment import + lexicon load are lazy (first use only) to keep this off
the module-import hot path.
"""
import re
from collections import Counter
from statistics import mean

from stockstalker.schemas import Article, NewsAnalysis
from stockstalker.utils import logger

_analyzer = None  # lazy singleton

# Tokens too generic to be useful as "themes".
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "for", "to", "of", "in", "on", "at",
    "by", "as", "is", "are", "was", "were", "be", "been", "it", "its", "this",
    "that", "with", "from", "into", "after", "over", "amid", "new", "says", "say",
    "said", "will", "has", "have", "had", "you", "your", "what", "why", "how",
    "could", "would", "should", "may", "more", "than", "stock", "stocks", "shares",
    "share", "inc", "corp", "report", "reports", "news", "today", "year",
}

_MAX_ARTICLES = 12  # VADER is cheap, but no need to score hundreds


def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def _compound(text: str) -> float:
    """VADER compound score for ``text`` — already in [-1, +1]."""
    return _get_analyzer().polarity_scores(text)["compound"]


def _keywords(articles: list[Article], ticker: str, k: int = 5) -> list[str]:
    """Cheap theme extraction: most frequent meaningful words across titles."""
    counts: Counter = Counter()
    skip = _STOPWORDS | {ticker.lower()}
    for article in articles:
        for tok in re.findall(r"[A-Za-z][A-Za-z&'-]{2,}", article.title or ""):
            low = tok.lower()
            if low not in skip:
                counts[low] += 1
    return [word.title() for word, _ in counts.most_common(k)]


def vader_news_analysis(ticker: str, articles: list[Article]) -> NewsAnalysis:
    """Build a NewsAnalysis from ``articles`` using VADER only (no LLM)."""
    selected = articles[:_MAX_ARTICLES]
    if not selected:
        return NewsAnalysis(
            sentiment_score=0.0,
            summary="No articles available for rule-based analysis.",
            what_changed="No data.",
        )

    scores = [_compound(f"{a.title}. {a.content or ''}"[:1000]) for a in selected]
    # mean of compound scores is in [-1, 1]; clamp defensively to the schema range.
    sentiment = max(-1.0, min(1.0, round(mean(scores), 3)))

    pos = sum(1 for s in scores if s > 0.05)
    neg = sum(1 for s in scores if s < -0.05)
    neu = len(scores) - pos - neg
    label = "bullish" if sentiment > 0.05 else "bearish" if sentiment < -0.05 else "neutral"

    summary = (
        f"Rule-based (VADER) sentiment across {len(selected)} recent headlines for "
        f"{ticker}: net {sentiment:+.2f} ({label}) — {pos} positive, {neu} neutral, "
        f"{neg} negative."
    )
    what_changed = (
        "Scored with the rule-based VADER engine — no AI summary or synthesis this run."
    )

    logger.info(
        "[VADER] {} -> sentiment {:+.2f} over {} articles", ticker, sentiment, len(selected)
    )
    return NewsAnalysis(
        selected_articles=selected,
        sentiment_score=sentiment,
        key_themes=_keywords(selected, ticker),
        summary=summary,
        what_changed=what_changed,
    )
