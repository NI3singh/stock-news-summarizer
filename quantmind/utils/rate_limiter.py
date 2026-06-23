"""QuantMind v2 — async rate limiter.

A time-based limiter enforcing both a per-second minimum interval and a
per-minute cap (tracked in a fixed-size ``deque``). Usable as an async context
manager (``async with limiter:``) or via ``await limiter.acquire()``.

An internal ``asyncio.Lock`` serialises the bookkeeping so the limiter stays
correct when many coroutines share it concurrently — without it, interleaved
check/sleep/append sequences across ``await`` points would over-issue calls.
"""
import asyncio
import time
from collections import deque


class AsyncRateLimiter:
    """Enforce calls_per_second (min interval) and calls_per_minute (window cap)."""

    def __init__(self, calls_per_second: float, calls_per_minute: int) -> None:
        self.calls_per_second = calls_per_second
        self.calls_per_minute = calls_per_minute
        self._calls: deque[float] = deque(maxlen=calls_per_minute)
        # The lock is created lazily and rebound per running loop: an asyncio.Lock
        # binds to the first loop it's used on and raises if reused from another
        # (the scheduler runs each daily job on a fresh event loop). Only the lock
        # is per-loop; the rate-limit state (_calls) is plain data shared across loops.
        self._lock: asyncio.Lock | None = None
        self._lock_loop: asyncio.AbstractEventLoop | None = None

    def _get_lock(self) -> asyncio.Lock:
        """Return a lock bound to the current running loop (recreate if it changed)."""
        loop = asyncio.get_running_loop()
        if self._lock is None or self._lock_loop is not loop:
            self._lock = asyncio.Lock()
            self._lock_loop = loop
        return self._lock

    async def acquire(self) -> None:
        """Block until a call is permitted under both limits, then record it."""
        async with self._get_lock():
            min_interval = 1.0 / self.calls_per_second
            now = time.monotonic()

            # Per-minute window: if the deque is full, wait until the oldest
            # recorded call is >60s old (i.e. leaves the rolling window).
            if self._calls.maxlen and len(self._calls) == self._calls.maxlen:
                wait = (self._calls[0] + 60.0) - now
                if wait > 0:
                    await asyncio.sleep(wait)
                    now = time.monotonic()

            # Per-second interval: space this call from the previous one.
            if self._calls:
                since_last = now - self._calls[-1]
                if since_last < min_interval:
                    await asyncio.sleep(min_interval - since_last)
                    now = time.monotonic()

            self._calls.append(now)

    async def __aenter__(self) -> "AsyncRateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        # No cleanup needed — the gate is released once acquire() returns.
        return None


# Named singletons tuned to each provider's free-tier limits.
gemini_limiter = AsyncRateLimiter(calls_per_second=0.9, calls_per_minute=55)
polygon_limiter = AsyncRateLimiter(calls_per_second=0.4, calls_per_minute=4)
scraper_limiter = AsyncRateLimiter(calls_per_second=1.0, calls_per_minute=30)
