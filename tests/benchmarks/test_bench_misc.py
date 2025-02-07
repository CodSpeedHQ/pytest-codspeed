import pytest


def count_even_fast(arr):
    """Count the number of even numbers in an array."""
    even = 0
    for x in arr:
        if x % 2 == 0:
            even += 1
    return even


def count_even_slow(arr):
    """Count the number of even numbers in an array."""
    return sum(1 for x in arr if x % 2 == 0)


@pytest.mark.parametrize(
    "func",
    [
        count_even_fast,
        count_even_slow,
    ],
)
def test_count_even(func, benchmark):
    assert benchmark(func, range(10_000)) == 5000


def sum_of_squares_for_loop_product(arr) -> int:
    total = 0
    for x in arr:
        total += x * x
    return total


def sum_of_squares_for_loop_power(arr) -> int:
    total = 0
    for x in arr:
        total += x**2
    return total


def sum_of_squares_sum_labmda_product(arr) -> int:
    return sum(map(lambda x: x * x, arr))  # noqa: C417


def sum_of_squares_sum_labmda_power(arr) -> int:
    return sum(map(lambda x: x**2, arr))  # noqa: C417


def sum_of_squares_sum_comprehension_product(arr) -> int:
    return sum(x * x for x in arr)


def sum_of_squares_sum_comprehension_power(arr) -> int:
    return sum(x**2 for x in arr)


@pytest.mark.parametrize(
    "func",
    [
        sum_of_squares_for_loop_product,
        sum_of_squares_for_loop_power,
        sum_of_squares_sum_labmda_product,
        sum_of_squares_sum_labmda_power,
        sum_of_squares_sum_comprehension_product,
        sum_of_squares_sum_comprehension_power,
    ],
)
@pytest.mark.benchmark
def test_sum_of_squares(func):
    assert func(range(1000)) == 332833500
