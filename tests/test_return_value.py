import pytest


@pytest.mark.benchmark
def test_return_value(benchmark):
    def calculate():
        return 1 + 1

    result = benchmark(calculate)

    assert result == 2
