"""StockStalker — alert condition evaluator (Phase B.5).

Evaluates the active ``AlertRule``s against a freshly produced ``TickerAnalysis``
and returns the alert messages that should be delivered (e.g. via the Telegram
bot's ``send_message``). Each fired rule is stamped (``last_triggered_at``) and
logged as an ``AlertEvent``. The OrchestratorAgent calls this after persisting an
analysis (wired in a later step).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from stockstalker.schemas import AlertConditionType, AlertEvent
from stockstalker.utils import logger

if TYPE_CHECKING:  # type-only imports
    from stockstalker.memory import DatabaseManager
    from stockstalker.schemas import TickerAnalysis


class AlertEngine:
    """Evaluates alert rules against new analyses and records fired events."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    async def evaluate(self, ticker: str, analysis: TickerAnalysis) -> list[str]:
        """Return the alert messages triggered by ``analysis`` (empty if none)."""
        rules = await self.db.get_active_alert_rules()
        messages: list[str] = []
        sentiment = analysis.news.sentiment_score

        for rule in rules:
            # Ticker-specific rules only fire for their ticker; ticker=None = any.
            if rule.ticker is not None and rule.ticker.upper() != ticker.upper():
                continue

            triggered_message: str | None = None

            if rule.condition_type == AlertConditionType.SENTIMENT_BELOW:
                if rule.threshold is not None and sentiment < rule.threshold:
                    triggered_message = (
                        f"⚠️ *Sentiment Alert — {ticker}*\n"
                        f"Sentiment dropped to {sentiment:+.2f} "
                        f"(threshold: {rule.threshold:+.2f})\n\n"
                        f"*What Changed:*\n{analysis.news.what_changed[:300]}"
                    )

            elif rule.condition_type == AlertConditionType.SENTIMENT_ABOVE:
                if rule.threshold is not None and sentiment > rule.threshold:
                    triggered_message = (
                        f"🚀 *Bullish Alert — {ticker}*\n"
                        f"Sentiment rose to {sentiment:+.2f} "
                        f"(threshold: {rule.threshold:+.2f})\n\n"
                        f"*Summary:*\n{analysis.news.summary[:300]}"
                    )

            elif rule.condition_type == AlertConditionType.NEW_SEC_FILING:
                # Dormant: the SEC EDGAR source was removed (re-adding it is on the
                # roadmap). Kept so the path works when EDGAR returns; the create-rule
                # UI no longer offers this condition for now.
                sec_articles = [
                    a
                    for a in analysis.news.selected_articles
                    if "SEC EDGAR" in a.source
                ]
                if sec_articles:
                    triggered_message = (
                        f"📄 *SEC Filing Alert — {ticker}*\n"
                        f"New filing detected: {sec_articles[0].title}\n"
                        f"Source: {sec_articles[0].source}"
                    )

            # NOTE: AlertConditionType.DAILY_SUMMARY is not a per-analysis
            # condition — it's delivered on a schedule (handled elsewhere).

            if triggered_message:
                await self.db.update_alert_last_triggered(rule.id)
                await self.db.log_alert_event(
                    AlertEvent(
                        rule_id=rule.id,
                        ticker=ticker,
                        message=triggered_message,
                        delivered=False,
                    )
                )
                messages.append(triggered_message)
                logger.info(
                    "alert triggered: {} / {}", ticker, rule.condition_type.value
                )

        return messages
