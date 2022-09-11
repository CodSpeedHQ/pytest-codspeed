from typing import Any, Callable

import pytest
from avalanche.callgrind_wrapper import lib


def pytest_addoption(parser: "pytest.Parser"):
    group = parser.getgroup("avalanche performance measurement")
    group.addoption(
        "--benchmark",
        action="store_true",
        default=False,
        help="Enable avalanche benchmarks",
    )
    group.addoption(
        "--only-benchmark",
        action="store_true",
        default=False,
        help="Only run avalanche benchmarks",
    )


def pytest_configure(config: "pytest.Config"):
    config.addinivalue_line(
        "markers", "avalanche_benchmark: mark an entire test for avalanche benchmarking"
    )
    config.addinivalue_line(
        "markers", "abenchmark: mark an entire test for avalanche benchmarking"
    )


@pytest.fixture(scope="session")
def _is_benchmark_enabled(request: "pytest.FixtureRequest") -> bool:
    return request.config.getoption("--benchmark")


@pytest.fixture
def callbench(
    request: "pytest.FixtureRequest", _is_benchmark_enabled: bool
) -> Callable:
    def run(func: Callable[..., Any], *args: Any):
        if _is_benchmark_enabled:
            lib.zero_stats()
            lib.start_instrumentation()
        func(*args)
        if _is_benchmark_enabled:
            lib.stop_instrumentation()
            lib.dump_stats_at(f"{request.node.nodeid}".encode("ascii"))

    return run


@pytest.fixture
def benchmark(callbench):
    """
    Compatibility with pytest-benchmark
    """
    return callbench
