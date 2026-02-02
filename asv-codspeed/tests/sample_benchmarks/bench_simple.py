"""Sample ASV benchmarks for testing asv-codspeed."""


def time_sum():
    """Benchmark summing a list."""
    total = sum(range(1000))
    return total


def time_list_comprehension():
    """Benchmark list comprehension."""
    result = [i**2 for i in range(100)]
    return result


class TimeSorting:
    """Benchmark sorting operations."""

    def setup(self):
        self.data = list(range(1000, 0, -1))

    def time_sort(self):
        sorted(self.data)

    def time_reverse(self):
        list(reversed(self.data))


class TimeParameterized:
    """Parameterized benchmarks."""

    params = [10, 100, 1000]
    param_names = ["n"]

    def time_range(self, n):
        for i in range(n):
            pass

    def time_sum(self, n):
        sum(range(n))
