"""Tests for the time formatting function."""

import pytest

from pytest_codspeed.instruments.walltime import format_time


@pytest.mark.parametrize(
    "time_ns,expected",
    [
        # Nanoseconds (< 1,000 ns)
        (0, "0ns"),
        (1, "1ns"),
        (123, "123ns"),
        (999, "999ns"),
        # Microseconds (1,000 ns - 999,999 ns)
        (1_000, "1.00µs"),
        (1_234, "1.23µs"),
        (10_500, "10.50µs"),
        (999_999, "1000.00µs"),
        # Milliseconds (1,000,000 ns - 999,999,999 ns)
        (1_000_000, "1.0ms"),
        (76_126_625, "76.1ms"),
        (75_860_833, "75.9ms"),
        (500_000_000, "500.0ms"),
        (999_999_999, "1000.0ms"),
        # Seconds (>= 1,000,000,000 ns)
        (1_000_000_000, "1.00s"),
        (2_500_000_000, "2.50s"),
        (10_000_000_000, "10.00s"),
    ],
)
def test_format_time(time_ns: float, expected: str) -> None:
    """Test that format_time correctly formats time values with appropriate units."""
    assert format_time(time_ns) == expected
