"""StockStalker v2 — daily scheduler (APScheduler AsyncIOScheduler).

Runs on the MAIN asyncio event loop (the same loop the Telegram bot polls on), so
scheduled jobs can await the async pipeline directly AND deliver Telegram messages
without cross-loop errors. ``start()`` must therefore be called from within a
running event loop (e.g. the async ``run-scheduler`` command).
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from stockstalker.config import settings
from stockstalker.utils import logger

if TYPE_CHECKING:  # import only for type-checkers — avoids any import-order risk
    from stockstalker.pipeline.runner import PipelineRunner


class DailyScheduler:
    """Runs the daily watchlist refresh (and optional Telegram summary) via cron.

    Uses AsyncIOScheduler so jobs execute on the current event loop — the same one
    the bot runs on — which lets scheduled alerts and the daily summary be sent
    over Telegram without the cross-loop issues a thread-based scheduler hits.
    """

    def __init__(self, runner: PipelineRunner) -> None:
        self.runner = runner
        self.scheduler = AsyncIOScheduler()
        self._timezone = pytz.timezone(settings.timezone)

    async def _job(self) -> None:
        """Daily refresh — runs on the event loop, so it just awaits the pipeline."""
        try:
            pairs = await self.runner.db.get_all_active_tickers()
            if not pairs:
                logger.warning("[scheduler] No active tickers — skipping refresh")
                return
            logger.info(
                "[scheduler] Starting daily refresh for {} tickers across {} users",
                len(pairs),
                len({uid for uid, _ in pairs}),
            )
            start = time.time()
            results = await self.runner.analyze_all(pairs)
            elapsed = time.time() - start
            logger.info(
                "[scheduler] Daily refresh complete: {}/{} succeeded in {:.1f}s",
                len(results),
                len(pairs),
                elapsed,
            )
        except Exception as exc:  # noqa: BLE001 — a job error must not kill the scheduler
            logger.error("[scheduler] Daily refresh failed: {}", exc)

    async def _summary_job(self) -> None:
        """Push the daily Telegram summary (only scheduled when the bot is enabled)."""
        try:
            if self.runner.bot is not None:
                await self.runner.bot.send_daily_summary()
        except Exception as exc:  # noqa: BLE001
            logger.error("[scheduler] Daily summary failed: {}", exc)

    def start(self) -> None:
        """Register the cron jobs and start the scheduler (call from a running loop)."""
        hour, minute = map(int, settings.refresh_time.split(":"))
        self.scheduler.add_job(
            self._job,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=self._timezone),
            id="daily_refresh",
            name="StockStalker Daily Refresh",
            replace_existing=True,
            misfire_grace_time=3600,
        )

        # Daily Telegram summary at 08:30 — only if the bot is wired up.
        if self.runner.bot is not None:
            self.scheduler.add_job(
                self._summary_job,
                trigger=CronTrigger(hour=8, minute=30, timezone=self._timezone),
                id="daily_summary",
                name="StockStalker Daily Summary",
                replace_existing=True,
                misfire_grace_time=3600,
            )

        self.scheduler.start()

        next_run = self.scheduler.get_job("daily_refresh").next_run_time
        logger.info(
            "[scheduler] Started — next refresh at {}",
            next_run.strftime("%Y-%m-%d %H:%M %Z"),
        )

    def stop(self) -> None:
        """Shut the scheduler down without waiting for running jobs."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("[scheduler] Stopped")
