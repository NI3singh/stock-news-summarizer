"""StockStalker — Telegram bot (Phase B).

Lives under ``stockstalker/integrations/`` (NOT ``stockstalker/telegram/``) on purpose:
``python-telegram-bot`` installs a top-level package named ``telegram``, and when
the app is run as ``python stockstalker/main.py`` the ``stockstalker/`` directory is on
``sys.path[0]`` — a ``stockstalker/telegram/`` folder there would shadow the real
library and break ``from telegram.ext import ...``. Naming it ``integrations``
avoids that entirely.

This is a thin wrapper that drives the shared ``PipelineRunner`` from Telegram
commands; it never re-implements analysis logic.
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from stockstalker.config import settings
from stockstalker.utils import logger

if TYPE_CHECKING:  # type-only imports — keep this module cheap & circular-safe
    from stockstalker.pipeline import PipelineRunner
    from stockstalker.schemas import TickerAnalysis


class StockStalkerBot:
    """Telegram front-end over the StockStalker pipeline."""

    def __init__(self, runner: PipelineRunner) -> None:
        self.runner = runner
        self.app = Application.builder().token(settings.telegram_bot_token).build()
        self._conflict_warned = False
        self._register_handlers()
        logger.info("StockStalkerBot initialized")

    @property
    def _uid(self) -> str:
        """The user this bot acts on behalf of (the deployer / OWNER_UID)."""
        return settings.effective_owner_uid

    def _register_handlers(self) -> None:
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("watchlist", self.cmd_watchlist))
        self.app.add_handler(CommandHandler("analyze", self.cmd_analyze))
        self.app.add_handler(CommandHandler("add", self.cmd_add))
        self.app.add_handler(CommandHandler("remove", self.cmd_remove))
        self.app.add_handler(CommandHandler("summary", self.cmd_summary))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    # --- Command handlers -----------------------------------------------------
    # /start /help /status /watchlist are implemented (B.2). /analyze /add
    # /remove + free-text are still stubs (B.3+). PTB v20+ runs handlers in the
    # bot's own event loop, so async DB calls are awaited directly.

    async def cmd_start(self, update, context) -> None:
        chat_id = update.effective_chat.id if update.effective_chat else "?"
        await update.message.reply_text(
            "🦅 *Welcome to StockStalker AI*\n\n"
            "I turn market news into clear, AI-analyzed intelligence — right here in "
            "Telegram. A team of agents reads the news, checks the charts, and writes "
            "you a plain-English report.\n\n"
            "*Try it now*\n"
            "• Send a ticker like `AAPL`  —  or  `/analyze AAPL`\n"
            "• `/add TSLA` to track it  ·  `/watchlist` to see what you track\n"
            "• `/summary` for a one-glance briefing\n\n"
            "Tap the *menu* (☰) next to the message box for every command, or /help.\n\n"
            f"_✅ Connected · your chat id is_ `{chat_id}`",
            parse_mode="Markdown",
        )

    async def cmd_help(self, update, context) -> None:
        await update.message.reply_text(
            "*How to use StockStalker* 🦅\n\n"
            "*Analyze*\n"
            "`/analyze AAPL` — full AI report: sentiment, what changed, signals\n"
            "_Tip: you can also just send a ticker like_ `TSLA`\n\n"
            "*Your watchlist*\n"
            "`/add NVDA` — start tracking a ticker\n"
            "`/remove NVDA` — stop tracking\n"
            "`/watchlist` — everything you track + latest sentiment\n\n"
            "*Briefings*\n"
            "`/summary` — one-glance summary of your whole watchlist\n"
            "`/status` — system health & next scheduled refresh\n\n"
            "I also *alert* you automatically when sentiment shifts sharply "
            "(configure rules in the web dashboard). Send /start anytime for the intro.",
            parse_mode="Markdown",
        )

    async def cmd_status(self, update, context) -> None:
        tickers = await self.runner.db.get_active_tickers(self._uid)
        analyses_today = 0
        for ticker in tickers:
            analyses_today += len(
                await self.runner.db.get_recent_analyses(self._uid, ticker, days=1)
            )
        await update.message.reply_text(
            "*System Status* ✅\n\n"
            f"Active tickers: {len(tickers)}\n"
            f"Analyses today: {analyses_today}\n"
            "Scheduler: Running\n"
            f"Next refresh: {settings.refresh_time} {settings.timezone}\n\n"
            "All systems operational.",
            parse_mode="Markdown",
        )

    async def cmd_watchlist(self, update, context) -> None:
        tickers = await self.runner.db.get_active_tickers(self._uid)
        if not tickers:
            await update.message.reply_text(
                "📋 Your watchlist is empty. Add tickers with /add AAPL"
            )
            return

        lines = ["*Your Watchlist*", ""]
        for ticker in tickers:
            recent = await self.runner.db.get_recent_analyses(self._uid, ticker, days=1)
            if not recent:
                lines.append(f"• {ticker}  |  no recent analysis")
                continue
            score = recent[0].get("sentiment_score")
            if score is None:
                emoji, score_str = "➡️", "n/a"
            else:
                emoji = "📈" if score > 0.2 else "📉" if score < -0.2 else "➡️"
                score_str = f"{score:+.2f}"
            when = self._fmt_when(recent[0].get("analyzed_at"))
            lines.append(
                f"• {ticker}  |  Sentiment: {score_str} {emoji}  |  Updated: {when}"
            )
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    @staticmethod
    def _fmt_when(raw: str | None) -> str:
        """Render a stored ISO ``analyzed_at`` as 'today HH:MM' or 'YYYY-MM-DD HH:MM' (UTC)."""
        if not raw:
            return "—"
        try:
            dt = datetime.fromisoformat(raw)
        except (ValueError, TypeError):
            return str(raw)[:16]
        today = datetime.now(timezone.utc).replace(tzinfo=None).date()
        if dt.date() == today:
            return f"today {dt.strftime('%H:%M')}"
        return dt.strftime("%Y-%m-%d %H:%M")

    async def cmd_analyze(self, update, context) -> None:
        if not context.args or not context.args[0].strip():
            await update.message.reply_text(
                "Please provide a ticker symbol. Example: /analyze AAPL"
            )
            return
        await self._analyze_and_reply(update, context.args[0].upper().strip())

    async def cmd_add(self, update, context) -> None:
        if not context.args:
            await update.message.reply_text(
                "Please provide a ticker symbol. Example: /add NVDA"
            )
            return
        ticker = context.args[0].upper().strip()
        if await self.runner.db.add_ticker(self._uid, ticker):
            await update.message.reply_text(
                f"✅ Added *{ticker}* to your watchlist. Running first analysis...",
                parse_mode="Markdown",
            )
            # Fire-and-forget so the user isn't blocked for ~30s.
            asyncio.create_task(self._bg_analyze(ticker))
        else:
            await update.message.reply_text(
                f"ℹ️ *{ticker}* is already in your watchlist.", parse_mode="Markdown"
            )

    async def cmd_remove(self, update, context) -> None:
        if not context.args:
            await update.message.reply_text(
                "Please provide a ticker symbol. Example: /remove NVDA"
            )
            return
        ticker = context.args[0].upper().strip()
        await self.runner.db.deactivate_ticker(self._uid, ticker)
        await update.message.reply_text(
            f"🗑️ Removed *{ticker}* from your watchlist.", parse_mode="Markdown"
        )

    async def cmd_summary(self, update, context) -> None:
        """On-demand watchlist briefing (same content as the scheduled daily push)."""
        await self._reply_markdown(update, await self._build_summary())

    async def handle_message(self, update, context) -> None:
        """Natural-language fallback for non-command text."""
        raw = (update.message.text or "").strip()
        low = raw.lower()
        if "watchlist" in low:
            await self.cmd_watchlist(update, context)
            return
        if "status" in low:
            await self.cmd_status(update, context)
            return
        if "analyze" in low or "analysis" in low:
            ticker = self._extract_ticker(raw)
            if ticker:
                await self._analyze_and_reply(update, ticker)
            else:
                await update.message.reply_text("Which ticker? e.g. analyze AAPL")
            return
        if re.fullmatch(r"[A-Z]{2,5}", raw):  # a bare uppercase ticker, e.g. AAPL
            await self._analyze_and_reply(update, raw)
            return
        await update.message.reply_text(
            "I'm not sure what you mean. Try /help to see what I can do, or just "
            "type a ticker like 'AAPL' to analyze it."
        )

    # --- internal helpers -----------------------------------------------------

    async def _analyze_and_reply(self, update, ticker: str) -> None:
        """Shared analysis path for /analyze and the natural-language handler."""
        await update.message.reply_text(
            f"🔄 Analyzing *{ticker}*... this takes ~30 seconds.",
            parse_mode="Markdown",
        )
        try:
            ta = await self.runner.analyze_ticker(self._uid, ticker)
        except Exception as exc:  # noqa: BLE001 — surface real failures to the user
            await update.message.reply_text(
                f"❌ Analysis failed for {ticker}: {str(exc)[:200]}"
            )
            return
        await self._reply_markdown(update, self._format_analysis(ta))

    async def _bg_analyze(self, ticker: str) -> None:
        """Fire-and-forget analysis (used by /add); logs instead of crashing."""
        try:
            await self.runner.analyze_ticker(self._uid, ticker)
        except Exception as exc:  # noqa: BLE001
            logger.warning("background analysis for {} failed: {}", ticker, exc)

    @staticmethod
    async def _reply_markdown(update, message: str) -> None:
        """Send Markdown, falling back to plain text if Telegram rejects the entities.

        LLM-generated text can contain stray ``* _ ` [`` that break Telegram's
        Markdown parser; without this a good analysis would surface as a send error.
        """
        try:
            await update.message.reply_text(message, parse_mode="Markdown")
        except Exception:  # noqa: BLE001 — parse/entity error -> resend as plain text
            await update.message.reply_text(message)

    @staticmethod
    def _extract_ticker(text: str) -> str | None:
        """Best-effort ticker extraction from free text."""
        m = re.search(r"\b[A-Z]{2,5}\b", text)  # explicit uppercase ticker wins
        if m:
            return m.group()
        parts = re.split(r"analy(?:ze|sis)", text, flags=re.IGNORECASE)
        if len(parts) > 1:
            stop = {"the", "of", "for", "stock", "please", "me", "my", "on"}
            for tok in re.findall(r"[A-Za-z]{2,5}", parts[1]):
                if tok.lower() not in stop:
                    return tok.upper()
        return None

    def _format_analysis(self, ta: TickerAnalysis) -> str:
        """Render a TickerAnalysis as a Telegram-Markdown message (*bold*, _italic_)."""
        score = ta.news.sentiment_score
        emoji = "🟢" if score > 0.3 else "🔴" if score < -0.3 else "⚪"
        sign = "+" if score > 0 else ""

        # quant is Optional, and each signal may be None — guard both.
        if ta.quant is not None:
            rsi = ta.quant.signals.rsi
            vol = ta.quant.signals.volume_ratio
            rsi_str = f"{rsi:.1f}" if rsi is not None else "N/A"
            vol_str = f"{vol:.1f}x" if vol is not None else "N/A"
        else:
            rsi_str, vol_str = "N/A", "N/A"

        summary = ta.news.summary or ""
        summary_disp = summary[:400] + ("..." if len(summary) > 400 else "")
        themes = ", ".join(ta.news.key_themes[:4])
        when = ta.analyzed_at.strftime("%b %d, %Y · %H:%M")

        return (
            f"📊 *{ta.ticker} Analysis*\n"
            f"_{when}_\n\n"
            f"*Sentiment:* {sign}{score:.2f} {emoji}\n"
            f"*Themes:* {themes}\n\n"
            f"⚡ *What Changed:*\n{ta.news.what_changed}\n\n"
            f"📝 *Summary:*\n{summary_disp}\n\n"
            f"📈 *Signals:* RSI {rsi_str} | Vol {vol_str}\n\n"
            f"_Analyzed by StockStalker's 4 AI agents_"
        )

    # --- Lifecycle ------------------------------------------------------------

    async def run_polling(self) -> None:
        await self.app.initialize()
        await self._setup_profile()
        await self.app.start()
        await self.app.updater.start_polling(
            drop_pending_updates=True, error_callback=self._on_poll_error
        )
        logger.info("Bot polling started")

    def _on_poll_error(self, exc: Exception) -> None:
        """Keep polling errors quiet + actionable — notably the 'two instances'
        Conflict you get when this bot token is polled in more than one place
        (e.g. running locally while the deployed app is also polling). Telegram
        allows only ONE getUpdates poller per token."""
        from telegram.error import Conflict

        if isinstance(exc, Conflict):
            if not self._conflict_warned:
                self._conflict_warned = True
                logger.warning(
                    "Telegram polling conflict: this bot token is already being polled "
                    "elsewhere (likely your deployed app). Run the bot in ONE place — "
                    "set ENABLE_BACKGROUND_JOBS=false here, or stop the other instance."
                )
        else:
            logger.warning("Telegram polling error: {}", exc)

    async def _setup_profile(self) -> None:
        """Register the slash-command menu + bot description shown in Telegram's UI.

        Best-effort — a failure here must never stop the bot from polling.
        """
        try:
            await self.app.bot.set_my_commands(
                [
                    BotCommand("analyze", "Full AI analysis — e.g. /analyze AAPL"),
                    BotCommand("watchlist", "Your tickers + latest sentiment"),
                    BotCommand("add", "Track a ticker — e.g. /add NVDA"),
                    BotCommand("remove", "Stop tracking a ticker"),
                    BotCommand("summary", "One-glance watchlist briefing"),
                    BotCommand("status", "System health & next refresh"),
                    BotCommand("help", "How to use this bot"),
                ]
            )
            await self.app.bot.set_my_short_description(
                "AI stock-news analysis — send a ticker (e.g. AAPL) for an instant report."
            )
            await self.app.bot.set_my_description(
                "StockStalker AI reads market news with a team of AI agents and sends "
                "you clear, plain-English stock reports.\n\n"
                "Send a ticker like AAPL (or /analyze AAPL) for an instant report, "
                "/add to track tickers, /summary for a daily briefing. Tap Start to begin."
            )
            logger.info("Telegram command menu + description registered")
        except Exception as exc:  # noqa: BLE001 — profile setup must not block polling
            logger.warning("Could not set Telegram bot profile: {}", exc)

    async def stop(self) -> None:
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        logger.info("Bot stopped")

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> None:
        if settings.telegram_chat_id is None:
            logger.warning("TELEGRAM_CHAT_ID not set — cannot send message")
            return
        await self.app.bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=text,
            parse_mode=parse_mode,
        )

    async def _build_summary(self) -> str:
        """One-line-per-ticker watchlist summary (shared by /summary and the daily push)."""
        tickers = await self.runner.db.get_active_tickers(self._uid)
        if not tickers:
            return "📋 Your watchlist is empty. Add a ticker with /add AAPL."
        lines = ["*📊 StockStalker Daily Summary*", ""]
        for ticker in tickers:
            analyses = await self.runner.db.get_recent_analyses(self._uid, ticker, days=1)
            if analyses:
                score = analyses[0].get("sentiment_score", 0.0) or 0.0
                emoji = "🟢" if score > 0.2 else "🔴" if score < -0.2 else "⚪"
                lines.append(f"{emoji} *{ticker}*: {score:+.2f}")
            else:
                lines.append(f"⚪ *{ticker}*: No data")
        lines.append(
            f"\n_Generated at {datetime.now(timezone.utc).strftime('%H:%M')} UTC_"
        )
        return "\n".join(lines)

    async def send_daily_summary(self) -> None:
        """Compose and push the daily watchlist summary to the configured chat."""
        tickers = await self.runner.db.get_active_tickers(self._uid)
        if not tickers:
            return
        await self.send_message(await self._build_summary())
