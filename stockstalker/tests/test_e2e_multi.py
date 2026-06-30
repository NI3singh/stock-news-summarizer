"""StockStalker v2 — multi-ticker concurrent e2e test (semaphore concurrency).

Marked ``live``. Run: pytest stockstalker/tests/test_e2e_multi.py -v -m live -s
Runs 3 tickers through analyze_all and shows they execute concurrently (all
acquire the semaphore and start together), printing a per-ticker results table.
NOTE: with 3 tickers and max_concurrent_tickers=3 nothing queues, so this
demonstrates concurrency but does not exercise the semaphore CAP (that would
need more tickers than the limit).
"""
import sys
import time

import pytest

from stockstalker.config.settings import DEV_UID
from stockstalker.pipeline import PipelineRunner

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):  # pragma: no cover — non-reconfigurable stream
    pass

pytestmark = pytest.mark.live


async def test_multi_ticker_concurrent():
    tickers = ["AAPL", "MSFT", "GOOGL"]

    runner = PipelineRunner()
    await runner.initialize()

    # Wrap analyze_ticker to record when each ticker actually starts.
    start_times: dict[str, float] = {}
    original_analyze = runner.analyze_ticker

    async def tracked_analyze(user_id, ticker):
        start_times[ticker] = time.time()
        return await original_analyze(user_id, ticker)

    runner.analyze_ticker = tracked_analyze

    start = time.time()
    results = await runner.analyze_all([(DEV_UID, t) for t in tickers])
    elapsed = time.time() - start

    # --- Basic assertions ---
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    for ta in results:
        assert ta.ticker in tickers
        assert len(ta.final_synthesis) > 50

    # --- Concurrency observation (printed, not asserted) ---
    start_times_list = sorted(start_times.values())
    if len(start_times_list) >= 2:
        first_start = start_times_list[0]
        last_start = start_times_list[-1]
        gap = last_start - first_start
        print(
            f"First start: {first_start - start:.1f}s, "
            f"Last start: {last_start - start:.1f}s, Gap: {gap:.1f}s"
        )

    # --- Performance: concurrent should be well under sequential ---
    assert elapsed < 180.0, f"Too slow: {elapsed:.1f}s"

    # --- Results table ---
    print("\n" + "=" * 60)
    print(f"{'TICKER':<10} {'SENTIMENT':>10} {'THEMES'}")
    print("-" * 60)
    for ta in results:
        print(f"{ta.ticker:<10} {ta.news.sentiment_score:>+.2f}        {', '.join(ta.news.key_themes[:2])}")
    print("=" * 60)
    print(f"Total elapsed: {elapsed:.1f}s for {len(tickers)} tickers")
    print("Multi-ticker concurrent test PASSED")
