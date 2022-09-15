from typing import Any, Callable, List

import pytest
from avalanche.callgrind_wrapper import lib

_benchmark_count = 0


@pytest.hookimpl()
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


@pytest.hookimpl()
def pytest_configure(config: "pytest.Config"):
    config.addinivalue_line(
        "markers", "avalanche_benchmark: mark an entire test for avalanche benchmarking"
    )
    config.addinivalue_line(
        "markers", "abenchmark: mark an entire test for avalanche benchmarking"
    )


def is_benchmark_enabled(config: "pytest.Config") -> bool:
    return config.getoption("--benchmark") or config.getoption("--only-benchmark")


def should_benchmark_item(item: "pytest.Item") -> bool:
    return (
        item.get_closest_marker("avalanche_benchmark") is not None
        or item.get_closest_marker("abenchmark") is not None
        or "benchmark" in getattr(item, "fixturenames", [])
    )


@pytest.hookimpl()
def pytest_sessionstart(session: "pytest.Session"):
    if is_benchmark_enabled(session.config):
        global _benchmark_count
        _benchmark_count = 0


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    session: "pytest.Session", config: "pytest.Config", items: "List[pytest.Item]"
):
    if config.getoption("--only-benchmark"):
        deselected = []
        selected = []
        for item in items:
            if should_benchmark_item(item):
                selected.append(item)
            else:
                deselected.append(item)
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected


@pytest.hookimpl()
def pytest_runtest_call(item: "pytest.Item"):
    if not is_benchmark_enabled(item.config) or not should_benchmark_item(item):
        item.runtest()
    else:
        global _benchmark_count
        _benchmark_count += 1
        if "benchmark" in getattr(item, "fixturenames", []):
            item.runtest()
        else:
            lib.zero_stats()
            lib.start_instrumentation()
            item.runtest()
            lib.stop_instrumentation()
            lib.dump_stats_at(f"{item.nodeid}".encode("ascii"))


@pytest.hookimpl()
def pytest_sessionfinish(session: "pytest.Session", exitstatus):
    if is_benchmark_enabled(session.config):
        reporter: pytest.TerminalReporter = session.config.pluginmanager.get_plugin(
            "terminalreporter"
        )
        reporter.write_sep("=", f"{_benchmark_count} benchmarked")


@pytest.fixture(scope="session")
def _is_benchmark_enabled(request: "pytest.FixtureRequest") -> bool:
    return is_benchmark_enabled(request.config)


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
