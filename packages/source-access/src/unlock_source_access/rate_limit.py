"""Async token bucket rate limiter.

Each connector gets its own TokenBucket instance, configured by
SourceConfig.rate_limit_per_second. The bucket refills continuously
(not in fixed windows), so short bursts are allowed as long as the
average rate stays under the limit.

Usage:
    bucket = TokenBucket(rate=5.0)  # 5 requests/second
    await bucket.acquire()          # blocks until a token is available
"""

import asyncio
import time


class TokenBucket:
    """Async token bucket that refills at a constant rate.

    The algorithm is simple: track the number of available tokens and the
    last time we checked. On each acquire(), calculate how many tokens have
    accumulated since the last check, add them (up to capacity), then consume
    one. If no tokens are available, sleep until one will be.
    """

    def __init__(self, rate: float, capacity: float | None = None) -> None:
        self.rate = rate
        self.capacity = capacity if capacity is not None else rate
        self.tokens = self.capacity
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        async with self._lock:
            self._refill()
            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self._refill()
            self.tokens -= 1.0

    def _refill(self) -> None:
        """Add tokens based on elapsed time since last refill."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self._last_refill = now
