"""Tests for the TokenBucket rate limiter.

Verifies:
  - Tokens are consumed correctly
  - Bucket refills over time
  - Acquire blocks when empty and resumes after refill
  - Custom capacity works
"""

import asyncio
import time

import pytest
from unlock_source_access.rate_limit import TokenBucket


async def test_initial_tokens():
    """Bucket starts full — capacity tokens available immediately."""
    bucket = TokenBucket(rate=10.0)
    assert bucket.tokens == 10.0


async def test_acquire_consumes_token():
    """Each acquire() removes one token."""
    bucket = TokenBucket(rate=10.0)
    await bucket.acquire()
    # Should have ~9 tokens (might be slightly more due to refill during acquire)
    assert bucket.tokens < 10.0


async def test_rapid_acquisition_drains_bucket():
    """Acquiring faster than the rate drains the bucket toward zero."""
    bucket = TokenBucket(rate=5.0, capacity=3.0)
    for _ in range(3):
        await bucket.acquire()
    # After 3 rapid acquires from a capacity-3 bucket, tokens should be near zero
    assert bucket.tokens < 1.0


async def test_acquire_blocks_when_empty():
    """When the bucket is empty, acquire() blocks until a token refills."""
    bucket = TokenBucket(rate=10.0, capacity=1.0)
    await bucket.acquire()  # Drain the single token

    start = time.monotonic()
    await bucket.acquire()  # Should block ~0.1s (1/rate)
    elapsed = time.monotonic() - start

    # Should have waited roughly 1/rate seconds (0.1s for rate=10)
    assert elapsed >= 0.05, f"Expected blocking wait, got {elapsed:.3f}s"


async def test_custom_capacity():
    """Capacity can be set independently from rate."""
    bucket = TokenBucket(rate=100.0, capacity=2.0)
    assert bucket.capacity == 2.0
    assert bucket.tokens == 2.0


async def test_refill_does_not_exceed_capacity():
    """Tokens never exceed capacity even after a long delay."""
    bucket = TokenBucket(rate=100.0, capacity=5.0)
    await bucket.acquire()
    await asyncio.sleep(0.1)  # Would refill 10 tokens at rate=100
    bucket._refill()
    assert bucket.tokens <= 5.0


@pytest.mark.parametrize(
    "rate,capacity",
    [
        (1.0, None),
        (5.0, 5.0),
        (10.0, 2.0),
        (100.0, 100.0),
        (0.5, 1.0),
    ],
)
async def test_various_configurations(rate: float, capacity: float | None):
    """TokenBucket works across a range of rate/capacity configurations."""
    bucket = TokenBucket(rate=rate, capacity=capacity)
    expected_cap = capacity if capacity is not None else rate
    assert bucket.capacity == expected_cap
    assert bucket.tokens == expected_cap
    await bucket.acquire()
    assert bucket.tokens < expected_cap
