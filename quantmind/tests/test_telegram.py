"""QuantMind — Telegram component unit tests (mocked; NO real Telegram calls).

Covers the alert engine (trigger / no-trigger / ticker filter), the analysis
message formatter, the daily summary, and the natural-language ticker routing.
The bot is built with a fake token (no network); send paths are mocked.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from quantmind.integrations.alert_engine import AlertEngine
from quantmind.integrations.telegram import QuantMindBot
from quantmind.schemas import (
    AlertConditionType,
    AlertRule,
    Article,
    MemoryContext,
    NewsAnalysis,
    QuantAnalysis,
    TechnicalSignals,
    TickerAnalysis,
)


def _mock_db(rules):
    """A stand-in DatabaseManager with the alert methods AlertEngine touches."""
    db = SimpleNamespace()
    db.get_active_alert_rules = AsyncMock(return_value=rules)
    db.update_alert_last_triggered = AsyncMock()
    db.log_alert_event = AsyncMock()
    return db


def _analysis(ticker="AAPL", sentiment=-0.8, sec=False):
    arts = (
        [Article(title="10-Q Filed", url="https://sec.gov/x", source="SEC EDGAR", ticker=ticker)]
        if sec
        else []
    )
    news = NewsAnalysis(
        sentiment_score=sentiment,
        key_themes=["Supply chain", "AI strategy"],
        what_changed="A notable change occurred in the company's outlook.",
        summary="A realistic multi-sentence summary of the day's events. " * 4,
        selected_articles=arts,
    )
    return TickerAnalysis(
        ticker=ticker,
        news=news,
        memory=MemoryContext(),
        quant=QuantAnalysis(signals=TechnicalSignals(rsi=55.0, volume_ratio=1.2)),
        final_synthesis="An overall synthesis fusing news and quant signals.",
    )


# --- Test 1: alert triggers on low sentiment -------------------------------
async def test_alert_triggers_on_low_sentiment():
    rule = AlertRule(id=1, ticker="AAPL", condition_type=AlertConditionType.SENTIMENT_BELOW, threshold=-0.4)
    engine = AlertEngine(_mock_db([rule]))
    msgs = await engine.evaluate("AAPL", _analysis("AAPL", -0.8))
    assert len(msgs) == 1
    assert "Sentiment Alert" in msgs[0]


# --- Test 2: no trigger above threshold ------------------------------------
async def test_alert_no_trigger_above_threshold():
    rule = AlertRule(id=1, ticker="AAPL", condition_type=AlertConditionType.SENTIMENT_BELOW, threshold=-0.4)
    engine = AlertEngine(_mock_db([rule]))
    msgs = await engine.evaluate("AAPL", _analysis("AAPL", 0.5))
    assert msgs == []


# --- Test 3: ticker filter -------------------------------------------------
async def test_alert_respects_ticker_filter():
    rule = AlertRule(id=1, ticker="MSFT", condition_type=AlertConditionType.SENTIMENT_BELOW, threshold=-0.4)
    engine = AlertEngine(_mock_db([rule]))
    msgs = await engine.evaluate("AAPL", _analysis("AAPL", -0.8))
    assert msgs == []


@pytest.fixture
def bot(monkeypatch):
    """A QuantMindBot built with a fake token (no network) + a stub runner."""
    from quantmind.config import settings

    monkeypatch.setattr(settings, "telegram_bot_token", "123456:FAKE-TOKEN-abcdefghij")
    monkeypatch.setattr(settings, "telegram_chat_id", "999")
    runner = SimpleNamespace(db=SimpleNamespace())
    return QuantMindBot(runner)


# --- Test 4: _format_analysis is Telegram-safe markdown --------------------
def test_format_analysis_telegram_safe(bot):
    msg = bot._format_analysis(_analysis("AAPL", 0.42))
    assert isinstance(msg, str)
    assert "*" in msg            # Telegram bold markers present
    assert "**" not in msg       # NOT Discord-style double-asterisk
    assert len(msg) < 4096       # Telegram message size limit


# --- Test 5: daily summary format ------------------------------------------
async def test_daily_summary_format(bot):
    bot.runner.db.get_active_tickers = AsyncMock(return_value=["AAPL", "MSFT"])
    bot.runner.db.get_recent_analyses = AsyncMock(return_value=[{"sentiment_score": 0.42}])
    bot.send_message = AsyncMock()

    await bot.send_daily_summary()

    bot.send_message.assert_called_once()
    sent = bot.send_message.call_args.args[0]
    assert "AAPL" in sent
    assert "MSFT" in sent


# --- Test 6: handle_message extracts a ticker from plain text --------------
async def test_handle_message_extracts_ticker(bot):
    # B.3 routes a bare ticker through the shared _analyze_and_reply helper
    # (not cmd_analyze), so assert that — it tests the same intent.
    bot._analyze_and_reply = AsyncMock()
    update = SimpleNamespace(message=SimpleNamespace(text="NVDA", reply_text=AsyncMock()))

    await bot.handle_message(update, None)

    bot._analyze_and_reply.assert_called_once()
    assert bot._analyze_and_reply.call_args.args[1] == "NVDA"
