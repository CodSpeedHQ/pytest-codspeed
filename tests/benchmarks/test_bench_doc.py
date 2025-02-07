"""Benches from the CodSpeed Getting Started Documentation."""

import pytest


def sum_of_squares_fast(arr) -> int:
    total = 0
    for x in arr:
        total += x * x
    return total


def sum_of_squares_slow(arr) -> int:
    return sum(map(lambda x: x**2, arr))  # noqa: C417


@pytest.mark.benchmark
def test_sum_squares_fast():
    assert sum_of_squares_fast(range(1000)) == 332833500


@pytest.mark.benchmark
def test_sum_squares_slow():
    assert sum_of_squares_slow(range(1000)) == 332833500
