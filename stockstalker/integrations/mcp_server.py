"""StockStalker — MCP server (Phase C).

Exposes the StockStalker pipeline to MCP clients (Claude Desktop, IDEs, etc.) via
FastMCP. Lives under ``stockstalker/integrations/`` (NOT ``stockstalker/mcp/``) on
purpose: FastMCP depends on the installed ``mcp`` SDK, and a top-level
``stockstalker/mcp/`` package would shadow it when the app runs as
``python stockstalker/main.py`` (``stockstalker/`` on ``sys.path[0]``).

Tools are registered on the module-level ``mcp`` instance in later steps; the
shared PipelineRunner is injected via ``set_runner()`` before the server serves.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastmcp import FastMCP

from stockstalker.config import settings
from stockstalker.utils import logger

if TYPE_CHECKING:  # type-only — the real runner is injected via set_runner()
    from stockstalker.pipeline import PipelineRunner


mcp = FastMCP(
    name="StockStalker",
    instructions="""
    You are connected to StockStalker — a multi-agent quantitative news intelligence system.

    This server gives you access to AI-powered stock market analysis. You can:
    - Retrieve the latest analysis for any ticker in the watchlist
    - Trigger a fresh analysis for any ticker
    - Get the full watchlist with sentiment scores
    - Compare multiple tickers side by side
    - Check the system health and recent agent activity

    All analysis data comes from a 4-agent pipeline: Memory Agent, News Agent (AI news analysis),
    Quant Agent (RSI, MACD, Bollinger Bands), and Orchestrator (synthesis).
    """,
)


# The shared PipelineRunner is injected before the server starts serving.
_runner: PipelineRunner | None = None


def set_runner(runner: PipelineRunner) -> None:
    global _runner
    _runner = runner
    logger.info("MCP server runner initialized")


def get_runner() -> PipelineRunner:
    if _runner is None:
        raise RuntimeError("Runner not initialized. Call set_runner() before serving.")
    return _runner


def _sentiment_label(score: float) -> str:
    return "Bullish" if score > 0.3 else "Bearish" if score < -0.3 else "Neutral"


# --- Tools (Phase C.2) -------------------------------------------------------

@mcp.tool()
async def get_stock_analysis(ticker: str) -> dict:
    """
    Get the most recent AI-generated analysis for a stock ticker.

    Returns the complete analysis including:
    - AI-generated summary of recent news
    - What changed since the last analysis
    - Sentiment score (-1.0 very negative to +1.0 very positive)
    - Key themes identified from news
    - Quantitative signals (RSI, MACD, volume ratio, price change)
    - Historical context from vector memory
    - List of source articles used

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL', 'MSFT', 'NVDA')

    Returns:
        dict with all analysis fields, or an error dict if no analysis exists.
    """
    runner = get_runner()
    ticker = ticker.upper().strip()

    analyses = await runner.db.get_recent_analyses(settings.effective_owner_uid, ticker, days=1)
    if not analyses:
        return {
            "error": f"No recent analysis found for {ticker}",
            "suggestion": f"Run run_stock_analysis('{ticker}') to generate a fresh analysis",
            "ticker": ticker,
        }

    latest = analyses[0]
    score = latest.get("sentiment_score") or 0.0

    # get_recent_analyses already JSON-decodes articles_used; tolerate a raw str.
    articles = latest.get("articles_used") or []
    if isinstance(articles, str):
        try:
            articles = json.loads(articles)
        except (ValueError, TypeError):
            articles = []

    return {
        "ticker": ticker,
        "analyzed_at": str(latest.get("analyzed_at", "")),
        "sentiment_score": score,
        "sentiment_label": _sentiment_label(score),
        "summary": latest.get("news_summary", ""),
        "what_changed": latest.get("what_changed", ""),
        "quant_interpretation": latest.get("quant_interpretation", ""),
        "final_synthesis": latest.get("final_synthesis", ""),
        "articles_used": articles,
    }


@mcp.tool()
async def run_stock_analysis(ticker: str) -> dict:
    """
    Trigger a fresh multi-agent analysis for a stock ticker right now.

    This runs the full 4-agent pipeline:
    1. Memory Agent — retrieves historical context
    2. News Agent — scrapes 4 sources and generates an AI summary
    3. Quant Agent — fetches price data and computes technical signals
    4. Orchestrator — synthesizes everything into a final report

    Takes 15-60 seconds to complete. The ticker does NOT need to be in your
    watchlist — you can analyze any publicly traded stock.

    Args:
        ticker: Stock ticker symbol (e.g. 'TSLA', 'GOOGL', 'AMZN')

    Returns:
        Complete analysis dict, or an error dict on failure.
    """
    runner = get_runner()
    ticker = ticker.upper().strip()
    logger.info("[MCP] run_stock_analysis called for {}", ticker)

    try:
        ta = await runner.analyze_ticker(settings.effective_owner_uid, ticker)
        score = ta.news.sentiment_score
        return {
            "ticker": ta.ticker,
            "analyzed_at": ta.analyzed_at.isoformat(),
            "sentiment_score": score,
            "sentiment_label": _sentiment_label(score),
            "key_themes": ta.news.key_themes,
            "summary": ta.news.summary,
            "what_changed": ta.news.what_changed,
            "final_synthesis": ta.final_synthesis,
            "quant_signals": {
                "rsi": ta.quant.signals.rsi if ta.quant else None,
                "macd": ta.quant.signals.macd if ta.quant else None,
                "volume_ratio": ta.quant.signals.volume_ratio if ta.quant else None,
                "price_change_pct": ta.quant.signals.price_change_pct if ta.quant else None,
            },
            "memory_context": {
                "days_of_history": ta.memory.days_of_history,
                "historical_trend": ta.memory.historical_sentiment_trend,
            },
            "articles_analyzed": len(ta.news.selected_articles),
            "sources": [a.source for a in ta.news.selected_articles],
        }
    except Exception as exc:  # noqa: BLE001 — surface failures as a tool error
        logger.error("[MCP] run_stock_analysis failed for {}: {}", ticker, exc)
        return {"error": str(exc), "ticker": ticker}


@mcp.tool()
async def get_watchlist() -> dict:
    """
    Get all tickers in the current watchlist with their latest sentiment scores
    and when they were last analyzed.

    Use this to understand which stocks are being tracked and their current
    market sentiment at a glance.

    Returns:
        dict with the list of tickers and their status.
    """
    runner = get_runner()
    tickers = await runner.db.get_active_tickers(settings.effective_owner_uid)
    if not tickers:
        return {"tickers": [], "count": 0, "message": "Watchlist is empty"}

    result = []
    for ticker in tickers:
        analyses = await runner.db.get_recent_analyses(settings.effective_owner_uid, ticker, days=1)
        if analyses:
            latest = analyses[0]
            score = latest.get("sentiment_score", None)
            result.append(
                {
                    "ticker": ticker,
                    "sentiment_score": score,
                    "sentiment_label": "Bullish"
                    if score and score > 0.3
                    else "Bearish"
                    if score and score < -0.3
                    else "Neutral",
                    "last_analyzed": str(latest.get("analyzed_at", "unknown")),
                }
            )
        else:
            result.append(
                {"ticker": ticker, "sentiment_score": None, "last_analyzed": "never"}
            )

    return {
        "tickers": result,
        "count": len(tickers),
        "most_bullish": max(result, key=lambda x: x["sentiment_score"] or -999)["ticker"]
        if result
        else None,
        "most_bearish": min(result, key=lambda x: x["sentiment_score"] or 999)["ticker"]
        if result
        else None,
    }


@mcp.tool()
async def compare_tickers(tickers: list[str]) -> dict:
    """
    Compare sentiment, themes, and signals across multiple tickers side by side.

    Useful for deciding which stocks have the strongest positive or negative
    signals today. Compare up to 5 tickers at once.

    Args:
        tickers: List of ticker symbols, e.g. ['AAPL', 'MSFT', 'GOOGL']

    Returns:
        Side-by-side comparison dict.
    """
    runner = get_runner()
    if len(tickers) > 5:
        return {"error": "Maximum 5 tickers for comparison"}

    comparison: dict = {}
    for ticker in tickers:
        ticker = ticker.upper().strip()
        analyses = await runner.db.get_recent_analyses(settings.effective_owner_uid, ticker, days=1)
        if analyses:
            latest = analyses[0]
            score = latest.get("sentiment_score", 0.0) or 0.0
            comparison[ticker] = {
                "sentiment_score": score,
                "sentiment_label": _sentiment_label(score),
                "what_changed": (latest.get("what_changed", "") or "")[:200],
                "analyzed_at": str(latest.get("analyzed_at", "")),
            }
        else:
            comparison[ticker] = {
                "error": f"No analysis available. Run run_stock_analysis('{ticker}') first."
            }

    valid = {k: v for k, v in comparison.items() if "sentiment_score" in v}
    ranking = sorted(valid.items(), key=lambda x: x[1]["sentiment_score"], reverse=True)

    return {
        "comparison": comparison,
        "ranking_by_sentiment": [r[0] for r in ranking],
        "strongest_buy_signal": ranking[0][0] if ranking else None,
        "strongest_sell_signal": ranking[-1][0] if ranking else None,
    }


@mcp.tool()
async def get_system_status() -> dict:
    """
    Get current system health: active tickers, database stats, the configured
    refresh schedule, and the vector-store size.

    Use this to understand whether the system is running correctly and when the
    next automatic refresh is configured.

    Returns:
        System health dict.
    """
    runner = get_runner()
    tickers = await runner.db.get_active_tickers(settings.effective_owner_uid)

    total_analyses = 0
    for ticker in tickers:
        analyses = await runner.db.get_recent_analyses(settings.effective_owner_uid, ticker, days=30)
        total_analyses += len(analyses)

    return {
        "status": "operational",
        "active_tickers": len(tickers),
        "watchlist": tickers,
        "total_analyses_30d": total_analyses,
        "scheduler_time": settings.refresh_time,
        "scheduler_timezone": settings.timezone,
        "vector_store_size": await runner.vector_store.collection_size(),
        "system_note": "StockStalker v2 — Multi-agent async pipeline. 4 agents: memory, news, quant, orchestrator.",
    }


# --- Serving (Phase C.4) -----------------------------------------------------

async def start_mcp_server(pipeline_runner: PipelineRunner) -> None:
    """Inject the shared runner and serve the MCP server over streamable HTTP."""
    set_runner(pipeline_runner)
    url = f"http://{settings.mcp_server_host}:{settings.mcp_server_port}/mcp"
    logger.info(
        "Starting MCP server on {}:{}",
        settings.mcp_server_host,
        settings.mcp_server_port,
    )
    logger.info("Connect Claude Desktop: Settings -> Developer -> MCP Servers -> Add")
    logger.info("  Name: StockStalker")
    logger.info("  URL: {}", url)
    await mcp.run_async(
        transport="streamable-http",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        path="/mcp",
    )
