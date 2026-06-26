"""StockStalker v2 — centralized prompt library.

The single source of truth for every prompt in the system. No prompt strings live
anywhere else in the `stockstalker` package. Each function returns a directive prompt
string; the JSON schema is appended for the structured-output calls (also serves
as guidance if a prompt is ever used with plain text generation).
"""
import json

from stockstalker.schemas import (
    Article,
    MemoryContext,
    NewsAnalysis,
    QuantAnalysis,
    TechnicalSignals,
    TickerAnalysis,
)


def news_select_prompt(ticker: str, articles: list[Article]) -> str:
    """Prompt to pick the 5-7 most valuable articles; returns a JSON index array."""
    listing = "\n".join(
        f"{idx}. [{a.source}] {a.title} (published: {a.published_at or 'N/A'})\n"
        f"   {a.content[:150]}"
        for idx, a in enumerate(articles, 1)
    )
    return (
        f"You are a financial analyst selecting the most valuable news for {ticker}.\n\n"
        f"From the numbered articles below, select the 5 to 7 that are most relevant, recent, "
        f"and from credible sources.\n"
        f"Prioritise: direct company news, earnings, regulatory filings, executive changes, "
        f"product launches.\n"
        f"Deprioritise: generic market commentary, duplicate coverage, vague sentiment pieces.\n\n"
        f"Articles:\n{listing}\n\n"
        f"Return ONLY a JSON array of the selected article index numbers (1-based), "
        f"e.g. [1, 3, 5, 7].\n"
        f"No explanation, no other text."
    )


def news_analyze_prompt(
    ticker: str, articles: list[Article], memory: MemoryContext | None
) -> str:
    """Prompt to produce a structured NewsAnalysis from the selected articles."""
    article_block = "\n\n".join(
        f"Title: {a.title}\nContent: {a.content or a.title}" for a in articles
    )

    historical = ""
    if memory is not None and memory.days_of_history > 0:
        events = "\n".join(f"- {e}" for e in memory.similar_past_events) or "- (none recorded)"
        historical = (
            f"\nHistorical Context (last {memory.days_of_history} days):\n"
            f"Sentiment trend: {memory.historical_sentiment_trend}\n"
            f"Similar past events:\n{events}\n"
        )

    schema_json = json.dumps(NewsAnalysis.model_json_schema(), indent=2)
    return (
        f"You are a financial analyst generating a structured daily news analysis for {ticker}.\n"
        f"Analyze the articles carefully and produce output matching the NewsAnalysis schema exactly.\n\n"
        f"Requirements:\n"
        f"- sentiment_score: float from -1.0 (very negative) to +1.0 (very positive), based on article tone.\n"
        f"- key_themes: 3-5 short phrases identifying the main topics.\n"
        f"- summary: a 300-400 word synthesis of key developments, facts, and market implications.\n"
        f"- what_changed: 80-100 words describing what is NEW compared to the historical context "
        f"(or 'First analysis — no prior history' if no history is provided).\n"
        f"- selected_articles: include the Article objects you were given (pass them through as-is).\n\n"
        f"Articles:\n{article_block}\n"
        f"{historical}\n"
        f"NewsAnalysis JSON schema:\n{schema_json}"
    )


def quant_interpret_prompt(
    ticker: str, signals: TechnicalSignals, news_sentiment: float
) -> str:
    """Prompt to interpret technical signals into a structured QuantAnalysis."""
    present = {k: v for k, v in signals.model_dump().items() if v is not None}
    signals_block = (
        "\n".join(f"- {name}: {value}" for name, value in present.items())
        or "- (no technical signals available)"
    )

    schema_json = json.dumps(QuantAnalysis.model_json_schema(), indent=2)
    return (
        f"You are a quantitative analyst interpreting technical signals for {ticker}.\n"
        f"news_sentiment is {news_sentiment} (scale: -1.0 very negative to +1.0 very positive).\n\n"
        f"Technical signals:\n{signals_block}\n\n"
        f"Requirements:\n"
        f"- interpretation: 150-200 word analysis of what the signals indicate about price momentum, "
        f"trend direction, and potential near-term moves.\n"
        f"- correlation_note: 60-80 words on whether the technical signals and news sentiment are "
        f"aligned or diverging, and what that typically implies.\n\n"
        f"QuantAnalysis JSON schema:\n{schema_json}"
    )


def synthesis_prompt(
    ticker: str,
    news: NewsAnalysis,
    quant: QuantAnalysis | None,
    memory: MemoryContext,
) -> str:
    """Prompt to synthesize news + quant + history into a final TickerAnalysis."""
    quant_text = quant.interpretation if quant is not None else "Data unavailable"
    historical = (
        f"{memory.historical_sentiment_trend} (over {memory.days_of_history} days of history)"
        if memory.days_of_history > 0
        else "No prior history"
    )

    schema_json = json.dumps(TickerAnalysis.model_json_schema(), indent=2)
    return (
        f"You are a senior analyst producing a final daily intelligence report for {ticker}.\n"
        f"Synthesize the news analysis and quantitative signals into a single coherent narrative.\n\n"
        f"News summary:\n{news.summary}\n\n"
        f"Quantitative interpretation:\n{quant_text}\n\n"
        f"Historical context:\n{historical}\n\n"
        f"Requirements:\n"
        f"- final_synthesis: 200-250 words.\n"
        f"- Address: what happened today, what the market data shows, whether the signals confirm or "
        f"contradict the news, and one clear takeaway for a trader monitoring this stock.\n"
        f"- Write in clear professional prose — no bullet points, no headers.\n\n"
        f"TickerAnalysis JSON schema:\n{schema_json}"
    )
