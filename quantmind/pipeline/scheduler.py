"""QuantMind v2 — daily scheduler (APScheduler BackgroundScheduler).

Wraps a timezone-aware cron trigger around the PipelineRunner. The scheduled job
runs in APScheduler's background thread, so it bridges into the async pipeline by
spinning up a dedicated event loop for the duration of the refresh.
"""
from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from quantmind.config import settings
from quantmind.utils import logger

if TYPE_CHECKING:  # import only for type-checkers — avoids any import-order risk
    from quantmind.pipeline.runner import PipelineRunner


class DailyScheduler:
    """Runs PipelineRunner.analyze_all for the watchlist once per day (cron)."""

    def __init__(self, runner: PipelineRunner) -> None:
        self.runner = runner
        self.scheduler = BackgroundScheduler()
        self._timezone = pytz.timezone(settings.timezone)

    def _job(self) -> None:
        """The scheduled refresh. Runs in APScheduler's background thread.

        BackgroundScheduler invokes this synchronously off the main thread, so we
        create a fresh event loop to drive the async pipeline, then close it.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tickers = loop.run_until_complete(self.runner.db.get_active_tickers())
            if not tickers:
                logger.warning("[scheduler] No active tickers — skipping refresh")
                return
            logger.info(
                "[scheduler] Starting daily refresh for {} tickers: {}",
                len(tickers),
                tickers,
            )
            start = time.time()
            results = loop.run_until_complete(self.runner.analyze_all(tickers))
            elapsed = time.time() - start
            logger.info(
                "[scheduler] Daily refresh complete: {}/{} succeeded in {:.1f}s",
                len(results),
                len(tickers),
                elapsed,
            )
        except Exception as exc:  # noqa: BLE001 — a job error must not kill the scheduler thread
            logger.error("[scheduler] Daily refresh failed: {}", exc)
        finally:
            loop.close()

    def start(self) -> None:
        """Register the daily cron job and start the background scheduler."""
        hour, minute = map(int, settings.refresh_time.split(":"))

        self.scheduler.add_job(
            self._job,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=self._timezone),
            id="daily_refresh",
            name="QuantMind Daily Refresh",
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
