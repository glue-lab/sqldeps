"""Rate limiting utilities for API calls.

This module provides classes for limiting the rate of API calls to stay
within provider limits, in both single-process and multi-process contexts.
"""

import time
from collections import deque
from multiprocessing.managers import SyncManager

from loguru import logger


class RateLimiter:
    """Rate limiter to prevent exceeding API rate limits.

    Tracks API call timestamps and enforces waiting periods
    to respect the specified requests per minute (RPM) limit.

    Attributes:
        rpm: Maximum requests per minute allowed
        call_times: Deque storing timestamps of recent API calls
        window: Time window in seconds (default: 60 seconds = 1 minute)
    """

    def __init__(self, rpm: int) -> None:
        """Initialize the rate limiter with an RPM limit.

        Args:
            rpm: Maximum number of API requests allowed per minute
        """
        self.rpm = rpm
        self.call_times = deque()
        self.window = 60  # 60 seconds =  1 minute window

    def wait_if_needed(self) -> None:
        """Ensures that calls do not exceed the rate limit.

        If the limit is reached, it waits until a slot is available.
        """
        if self.rpm <= 0:  # Disable rate limiting if rpm is 0
            return

        now = time.time()

        # Remove timestamps older than our time window (60 seconds)
        cutoff = now - self.window
        while self.call_times and self.call_times[0] < cutoff:
            self.call_times.popleft()

        # If we've reached the RPM limit, wait until the oldest timestamp expires
        if len(self.call_times) >= self.rpm:
            wait_time = max(0, self.call_times[0] + self.window - now)
            if wait_time > 0:
                logger.debug(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)

                # After waiting, recalculate current time and clean up again
                now = time.time()
                cutoff = now - self.window
                while self.call_times and self.call_times[0] < cutoff:
                    self.call_times.popleft()

        # Record this API call's timestamp
        self.call_times.append(now)


class MultiprocessingRateLimiter:
    """A shared rate limiter for multiprocessing environments.

    Uses a manager to share state between processes, ensuring
    all processes collectively respect the RPM limit.

    Attributes:
        call_times: A shared list of API call timestamps
        lock: A shared lock for thread-safe operations
        rpm: Maximum requests per minute allowed
        window: Time window in seconds
    """

    def __init__(self, manager: SyncManager, rpm: int) -> None:
        """Initialize with a multiprocessing manager and RPM limit.

        Args:
            manager: A multiprocessing.Manager instance
            rpm: Maximum requests per minute allowed
        """
        self.call_times = manager.list()
        self.lock = manager.RLock()
        self.rpm = rpm
        self.window = 60

    def wait_if_needed(self) -> None:
        """Ensures calls don't exceed the rate limit across processes."""
        if self.rpm <= 0:
            return

        with self.lock:
            now = time.time()
            cutoff = now - self.window

            # Remove old timestamps
            while self.call_times and self.call_times[0] < cutoff:
                self.call_times.pop(0)

            # Wait if at RPM limit
            if len(self.call_times) >= self.rpm:
                wait_time = max(0, self.call_times[0] + self.window - now)
                if wait_time > 0:
                    logger.debug(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                    time.sleep(wait_time)

                    # Recalculate after waiting
                    now = time.time()
                    cutoff = now - self.window
                    while self.call_times and self.call_times[0] < cutoff:
                        self.call_times.pop(0)

            # Record this call
            self.call_times.append(now)
