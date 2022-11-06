import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, List, Optional

import pytest

from . import __version__
from ._wrapper import get_lib

if TYPE_CHECKING:
    from ._wrapper import LibType


@pytest.hookimpl(trylast=True)
def pytest_addoption(parser: "pytest.Parser"):
    group = parser.getgroup("CodSpeed benchmarking")
    group.addoption(
        "--codspeed",
        action="store_true",
        default=False,
        help="Enable codspeed (not required when using the CodSpeed action)",
    )


@dataclass(unsafe_hash=True)
class CodSpeedPlugin:
    is_codspeed_enabled: bool
    should_measure: bool
    lib: Optional["LibType"] = None
    benchmark_count: int = 0


PLUGIN_NAME = "codspeed_plugin"


def get_plugin(config: "pytest.Config") -> "CodSpeedPlugin":
    return config.pluginmanager.get_plugin(PLUGIN_NAME)


@pytest.hookimpl()
def pytest_configure(config: "pytest.Config"):
    config.addinivalue_line(
        "markers", "codspeed_benchmark: mark an entire test for codspeed benchmarking"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark an entire test for codspeed benchmarking"
    )
    plugin = CodSpeedPlugin(
        is_codspeed_enabled=config.getoption("--codspeed")
        or os.environ.get("CODSPEED_ENV") is not None,
        should_measure=os.environ.get("CODSPEED_ENV") is not None,
    )
    if plugin.should_measure:
        plugin.lib = get_lib()
    config.pluginmanager.register(plugin, PLUGIN_NAME)


@pytest.hookimpl(trylast=True)
def pytest_report_header(config: "pytest.Config"):
    out = [f"codspeed: {__version__}"]
    plugin = get_plugin(config)
    if plugin.is_codspeed_enabled and not plugin.should_measure:
        out.append(
            "NOTICE: codspeed is enabled, but no performance measurement"
            " will be made since it's running in an unknown environment."
        )
    return "\n".join(out)


def should_benchmark_item(item: "pytest.Item") -> bool:
    return (
        item.get_closest_marker("codspeed_benchmark") is not None
        or item.get_closest_marker("benchmark") is not None
        or "benchmark" in getattr(item, "fixturenames", [])
    )


@pytest.hookimpl()
def pytest_sessionstart(session: "pytest.Session"):
    plugin = get_plugin(session.config)
    if plugin.is_codspeed_enabled:
        plugin.benchmark_count = 0


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    session: "pytest.Session", config: "pytest.Config", items: "List[pytest.Item]"
):
    plugin = get_plugin(config)
    if plugin.is_codspeed_enabled:
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
    plugin = get_plugin(item.config)
    if not plugin.is_codspeed_enabled or not should_benchmark_item(item):
        item.runtest()
    else:
        plugin.benchmark_count += 1
        if "benchmark" in getattr(item, "fixturenames", []):
            # This is a benchmark fixture, so the measurement is done by the fixture
            item.runtest()
        elif not plugin.should_measure:
            item.runtest()
        else:
            assert plugin.lib is not None
            plugin.lib.zero_stats()
            plugin.lib.start_instrumentation()
            item.runtest()
            plugin.lib.stop_instrumentation()
            plugin.lib.dump_stats_at(f"{item.nodeid}".encode("ascii"))


@pytest.hookimpl()
def pytest_sessionfinish(session: "pytest.Session", exitstatus):
    plugin = get_plugin(session.config)
    if plugin.is_codspeed_enabled:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        count_suffix = "benchmarked" if plugin.should_measure else "benchmark tested"
        reporter.write_sep(
            "=",
            f"{plugin.benchmark_count} {count_suffix}",
        )


@pytest.fixture
def codspeed_benchmark(request: "pytest.FixtureRequest") -> Callable:
    plugin = get_plugin(request.config)

    def run(func: Callable[..., Any], *args: Any):
        if plugin.is_codspeed_enabled and plugin.should_measure:
            assert plugin.lib is not None
            plugin.lib.zero_stats()
            plugin.lib.start_instrumentation()
            func(*args)
            plugin.lib.stop_instrumentation()
            plugin.lib.dump_stats_at(f"{request.node.nodeid}".encode("ascii"))
        else:
            func(*args)

    return run


@pytest.fixture
def benchmark(codspeed_benchmark):
    """
    Compatibility with pytest-benchmark
    """
    return codspeed_benchmark
