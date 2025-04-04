"""Unit tests for rate limiter.

This module tests the rate limiting functionality which is used to control
the frequency of API calls to LLM providers.
"""

from unittest.mock import MagicMock, patch

from sqldeps.rate_limiter import MultiprocessingRateLimiter, RateLimiter


def test_rate_limiter_no_wait_under_limit() -> None:
    """Test rate limiter when under the RPM limit (no waiting needed)."""
    # Create a rate limiter with 60 RPM (1 request per second)
    limiter = RateLimiter(rpm=60)

    # Mock time.time to return controlled values
    with patch("time.time", return_value=100), patch("time.sleep") as mock_sleep:
        # Call wait_if_needed multiple times (less than rpm)
        for _ in range(30):
            limiter.wait_if_needed()

        # Verify sleep was not called since we're under the rate limit
        mock_sleep.assert_not_called()


def test_rate_limiter_wait_when_limit_reached() -> None:
    """Test rate limiter when RPM limit is reached (should wait)."""
    # Create a rate limiter with 10 RPM
    limiter = RateLimiter(rpm=10)

    # Set up the call_times list with timestamps that would trigger rate limiting
    current_time = 100
    limiter.call_times = [
        current_time - 50 + i for i in range(10)
    ]  # 10 calls in last 50 seconds

    # Mock time functions
    with (
        patch("time.time", return_value=current_time),
        patch("time.sleep") as mock_sleep,
    ):
        # This call should trigger waiting since we've reached 10 calls in the window
        limiter.wait_if_needed()

        # Verify sleep was called with the correct wait time (should wait ~10 seconds)
        # First timestamp is (current_time - 50), so it expires at (current_time + 10)
        expected_wait_time = 10  # (current_time - 50) + 60 - current_time
        mock_sleep.assert_called_once()
        actual_wait_time = mock_sleep.call_args[0][0]
        assert (
            abs(actual_wait_time - expected_wait_time) < 0.01
        )  # Allow small float differences


def test_rate_limiter_zero_rpm() -> None:
    """Test rate limiter when RPM is set to zero (disabled)."""
    limiter = RateLimiter(rpm=0)

    with patch("time.time") as mock_time, patch("time.sleep") as mock_sleep:
        # Call wait_if_needed multiple times
        for _ in range(100):
            limiter.wait_if_needed()

        # Verify that time and sleep were not called
        mock_time.assert_not_called()
        mock_sleep.assert_not_called()


def test_multiprocessing_rate_limiter() -> None:
    """Test multiprocessing rate limiter."""
    # Create a mock manager
    mock_manager = MagicMock()
    mock_manager.list.return_value = []
    mock_manager.RLock.return_value = MagicMock()

    # Create limiter with mock manager
    limiter = MultiprocessingRateLimiter(mock_manager, rpm=10)

    # Test wait_if_needed when under the limit
    with patch("time.time", return_value=100), patch("time.sleep") as mock_sleep:
        limiter.wait_if_needed()

        # Since there are no previous calls, sleep should not be called
        mock_sleep.assert_not_called()

        # call_times should have been updated
        assert len(limiter.call_times) == 1
        assert limiter.call_times[0] == 100
