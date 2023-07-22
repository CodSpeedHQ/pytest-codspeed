import gc
import os
import pkgutil
import sys
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import pytest
from _pytest.fixtures import FixtureManager

from . import __version__
from ._wrapper import get_lib

if TYPE_CHECKING:
    from ._wrapper import LibType

IS_PYTEST_BENCHMARK_INSTALLED = pkgutil.find_loader("pytest_benchmark") is not None
SUPPORTS_PERF_TRAMPOLINE = sys.version_info >= (3, 12)


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
    lib: Optional["LibType"]
    disabled_plugins: Tuple[str, ...]
    benchmark_count: int = field(default=0, hash=False, compare=False)


PLUGIN_NAME = "codspeed_plugin"


def get_plugin(config: "pytest.Config") -> "CodSpeedPlugin":
    return config.pluginmanager.get_plugin(PLUGIN_NAME)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: "pytest.Config"):
    config.addinivalue_line(
        "markers", "codspeed_benchmark: mark an entire test for codspeed benchmarking"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark an entire test for codspeed benchmarking"
    )
    is_codspeed_enabled = (
        config.getoption("--codspeed") or os.environ.get("CODSPEED_ENV") is not None
    )
    should_measure = os.environ.get("CODSPEED_ENV") is not None
    lib = get_lib() if should_measure else None
    if lib is not None:
        lib.dump_stats_at(f"Metadata: pytest-codspeed {__version__}".encode("ascii"))
    disabled_plugins: List[str] = []
    # Disable pytest-benchmark if codspeed is enabled
    if is_codspeed_enabled and IS_PYTEST_BENCHMARK_INSTALLED:
        object.__setattr__(config.option, "benchmark_disable", True)
        config.pluginmanager.set_blocked("pytest-benchmark")
        disabled_plugins.append("pytest-benchmark")

    plugin = CodSpeedPlugin(
        is_codspeed_enabled=is_codspeed_enabled,
        should_measure=should_measure,
        lib=lib,
        disabled_plugins=tuple(disabled_plugins),
    )
    config.pluginmanager.register(plugin, PLUGIN_NAME)


def pytest_plugin_registered(plugin, manager: "pytest.PytestPluginManager"):
    """Patch the benchmark fixture to use the codspeed one if codspeed is enabled"""
    if IS_PYTEST_BENCHMARK_INSTALLED and isinstance(plugin, FixtureManager):
        fixture_manager = plugin
        codspeed_plugin: CodSpeedPlugin = manager.get_plugin(PLUGIN_NAME)
        if codspeed_plugin.is_codspeed_enabled:
            codspeed_benchmark_fixtures = plugin.getfixturedefs(
                "codspeed_benchmark", ""
            )
            assert codspeed_benchmark_fixtures is not None
            fixture_manager._arg2fixturedefs[
                "__benchmark"
            ] = fixture_manager._arg2fixturedefs["benchmark"]
            fixture_manager._arg2fixturedefs["benchmark"] = list(
                codspeed_benchmark_fixtures
            )


@pytest.hookimpl(trylast=True)
def pytest_report_header(config: "pytest.Config"):
    out = [
        f"codspeed: {__version__} "
        f"(callgraph: {'enabled' if SUPPORTS_PERF_TRAMPOLINE  else 'not supported'})"
    ]
    plugin = get_plugin(config)
    if plugin.is_codspeed_enabled and not plugin.should_measure:
        out.append(
            "\033[1m"
            "NOTICE: codspeed is enabled, but no performance measurement"
            " will be made since it's running in an unknown environment."
            "\033[0m"
        )
    if len(plugin.disabled_plugins) > 0:
        out.append(
            "\033[93mCodSpeed had to disable the following plugins: "
            f"{', '.join(plugin.disabled_plugins)}\033[0m"
        )
    return "\n".join(out)


def has_benchmark_fixture(item: "pytest.Item") -> bool:
    item_fixtures = getattr(item, "fixturenames", [])
    return "benchmark" in item_fixtures or "codspeed_benchmark" in item_fixtures


def has_benchmark_marker(item: "pytest.Item") -> bool:
    return (
        item.get_closest_marker("codspeed_benchmark") is not None
        or item.get_closest_marker("benchmark") is not None
    )


def should_benchmark_item(item: "pytest.Item") -> bool:
    return has_benchmark_fixture(item) or has_benchmark_marker(item)


@pytest.hookimpl()
def pytest_sessionstart(session: "pytest.Session"):
    plugin = get_plugin(session.config)
    if plugin.is_codspeed_enabled:
        plugin.benchmark_count = 0
        if plugin.should_measure and SUPPORTS_PERF_TRAMPOLINE:
            sys.activate_stack_trampoline("perf")  # type: ignore


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


def _run_with_instrumentation(
    lib: "LibType", nodeId: str, fn: Callable[..., Any], *args, **kwargs
):
    is_gc_enabled = gc.isenabled()
    if is_gc_enabled:
        gc.collect()
        gc.disable()

    result = None

    def __codspeed_root_frame__():
        nonlocal result
        result = fn(*args, **kwargs)

    if SUPPORTS_PERF_TRAMPOLINE:
        # Warmup CPython performance map cache
        __codspeed_root_frame__()

    lib.zero_stats()
    lib.start_instrumentation()
    __codspeed_root_frame__()
    lib.stop_instrumentation()
    lib.dump_stats_at(f"{nodeId}".encode("ascii"))
    if is_gc_enabled:
        gc.enable()

    return result


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item: "pytest.Item", nextitem: Union["pytest.Item", None]):
    plugin = get_plugin(item.config)
    if not plugin.is_codspeed_enabled or not should_benchmark_item(item):
        return (
            None  # Defer to the default test protocol since no benchmarking is needed
        )

    if has_benchmark_fixture(item):
        return None  # Instrumentation is handled by the fixture

    plugin.benchmark_count += 1
    if not plugin.should_measure:
        return None  # Benchmark counted but will be run in the default protocol

    # Setup phase
    reports = []
    ihook = item.ihook
    ihook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)
    setup_call = pytest.CallInfo.from_call(
        lambda: ihook.pytest_runtest_setup(item=item, nextitem=nextitem), "setup"
    )
    setup_report = ihook.pytest_runtest_makereport(item=item, call=setup_call)
    ihook.pytest_runtest_logreport(report=setup_report)
    reports.append(setup_report)
    # Run phase
    if setup_report.passed and not item.config.getoption("setuponly"):
        assert plugin.lib is not None
        runtest_call = pytest.CallInfo.from_call(
            lambda: _run_with_instrumentation(plugin.lib, item.nodeid, item.runtest),
            "call",
        )
        runtest_report = ihook.pytest_runtest_makereport(item=item, call=runtest_call)
        ihook.pytest_runtest_logreport(report=runtest_report)
        reports.append(runtest_report)

    # Teardown phase
    teardown_call = pytest.CallInfo.from_call(
        lambda: ihook.pytest_runtest_teardown(item=item, nextitem=nextitem), "teardown"
    )
    teardown_report = ihook.pytest_runtest_makereport(item=item, call=teardown_call)
    ihook.pytest_runtest_logreport(report=teardown_report)
    reports.append(teardown_report)
    ihook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)

    return reports  # Deny further protocol hooks execution


T = TypeVar("T")


class BenchmarkFixture:
    """The fixture that can be used to benchmark a function."""

    def __init__(self, request: "pytest.FixtureRequest"):
        self.extra_info: Dict = {}

        self._request = request

    def __call__(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        plugin = get_plugin(self._request.config)
        plugin.benchmark_count += 1
        if plugin.is_codspeed_enabled and plugin.should_measure:
            assert plugin.lib is not None
            return _run_with_instrumentation(
                plugin.lib, self._request.node.nodeid, func, *args, **kwargs
            )
        else:
            return func(*args, **kwargs)


@pytest.fixture(scope="function")
def codspeed_benchmark(request: "pytest.FixtureRequest") -> Callable:
    return BenchmarkFixture(request)


if not IS_PYTEST_BENCHMARK_INSTALLED:

    @pytest.fixture(scope="function")
    def benchmark(codspeed_benchmark, request: "pytest.FixtureRequest"):
        """
        Compatibility with pytest-benchmark
        """
        return codspeed_benchmark


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
