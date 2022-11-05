import os
from typing import Any, Callable, List

import pytest

from . import __version__
from ._wrapper import get_lib

lib = get_lib()

_benchmark_count = 0


@pytest.hookimpl(trylast=True)
def pytest_report_header(config: "pytest.Config"):
    return f"codspeed: {__version__}"


@pytest.hookimpl(trylast=True)
def pytest_addoption(parser: "pytest.Parser"):
    group = parser.getgroup("CodSpeed benchmarking")
    group.addoption(
        "--codspeed",
        action="store_true",
        default=False,
        help="Enable codspeed (not required when using the CodSpeed action)",
    )


@pytest.hookimpl()
def pytest_configure(config: "pytest.Config"):
    config.addinivalue_line(
        "markers", "codspeed_benchmark: mark an entire test for codspeed benchmarking"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark an entire test for codspeed benchmarking"
    )


def is_benchmark_enabled(config: "pytest.Config") -> bool:
    return config.getoption("--codspeed") or os.environ.get("CODSPEED_ENV") is not None


def should_benchmark_item(item: "pytest.Item") -> bool:
    return (
        item.get_closest_marker("codspeed_benchmark") is not None
        or item.get_closest_marker("benchmark") is not None
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
    if is_benchmark_enabled(session.config):
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
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        reporter.write_sep("=", f"{_benchmark_count} benchmarked")


@pytest.fixture(scope="session")
def _is_benchmark_enabled(request: "pytest.FixtureRequest") -> bool:
    return is_benchmark_enabled(request.config)


@pytest.fixture
def codspeed_benchmark(
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
def benchmark(codspeed_benchmark):
    """
    Compatibility with pytest-benchmark
    """
    return codspeed_benchmark
