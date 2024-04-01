from __future__ import annotations

import functools
import gc
import os
import pkgutil
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest
from _pytest.fixtures import FixtureManager

from pytest_codspeed.utils import get_git_relative_uri

from . import __version__
from ._wrapper import get_lib

if TYPE_CHECKING:
    from typing import Any, Callable, ParamSpec, TypeVar

    from ._wrapper import LibType

    T = TypeVar("T")
    P = ParamSpec("P")

IS_PYTEST_BENCHMARK_INSTALLED = pkgutil.find_loader("pytest_benchmark") is not None
SUPPORTS_PERF_TRAMPOLINE = sys.version_info >= (3, 12)
BEFORE_PYTEST_8_1_1 = pytest.version_tuple < (8, 1, 1)


@pytest.hookimpl(trylast=True)
def pytest_addoption(parser: pytest.Parser):
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
    lib: LibType | None
    disabled_plugins: tuple[str, ...]
    benchmark_count: int = field(default=0, hash=False, compare=False)


PLUGIN_NAME = "codspeed_plugin"


def get_plugin(config: pytest.Config) -> CodSpeedPlugin:
    return config.pluginmanager.get_plugin(PLUGIN_NAME)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config):
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
    disabled_plugins: list[str] = []
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


def pytest_plugin_registered(plugin, manager: pytest.PytestPluginManager):
    """Patch the benchmark fixture to use the codspeed one if codspeed is enabled"""
    if IS_PYTEST_BENCHMARK_INSTALLED and isinstance(plugin, FixtureManager):
        fixture_manager = plugin
        codspeed_plugin: CodSpeedPlugin = manager.get_plugin(PLUGIN_NAME)
        if codspeed_plugin.is_codspeed_enabled:
            codspeed_benchmark_fixtures = plugin.getfixturedefs(
                "codspeed_benchmark",
                fixture_manager.session.nodeid
                if BEFORE_PYTEST_8_1_1
                else fixture_manager.session,
            )
            assert codspeed_benchmark_fixtures is not None
            # Archive the pytest-benchmark fixture
            fixture_manager._arg2fixturedefs["__benchmark"] = (
                fixture_manager._arg2fixturedefs["benchmark"]
            )
            # Replace the pytest-benchmark fixture with the codspeed one
            fixture_manager._arg2fixturedefs["benchmark"] = codspeed_benchmark_fixtures


@pytest.hookimpl(trylast=True)
def pytest_report_header(config: pytest.Config):
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


def has_benchmark_fixture(item: pytest.Item) -> bool:
    item_fixtures = getattr(item, "fixturenames", [])
    return "benchmark" in item_fixtures or "codspeed_benchmark" in item_fixtures


def has_benchmark_marker(item: pytest.Item) -> bool:
    return (
        item.get_closest_marker("codspeed_benchmark") is not None
        or item.get_closest_marker("benchmark") is not None
    )


def should_benchmark_item(item: pytest.Item) -> bool:
    return has_benchmark_fixture(item) or has_benchmark_marker(item)


@pytest.hookimpl()
def pytest_sessionstart(session: pytest.Session):
    plugin = get_plugin(session.config)
    if plugin.is_codspeed_enabled:
        plugin.benchmark_count = 0
        if plugin.should_measure and SUPPORTS_PERF_TRAMPOLINE:
            sys.activate_stack_trampoline("perf")  # type: ignore


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
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
    lib: LibType,
    nodeid: str,
    config: pytest.Config,
    fn: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    is_gc_enabled = gc.isenabled()
    if is_gc_enabled:
        gc.collect()
        gc.disable()

    def __codspeed_root_frame__() -> T:
        return fn(*args, **kwargs)

    try:
        if SUPPORTS_PERF_TRAMPOLINE:
            # Warmup CPython performance map cache
            __codspeed_root_frame__()

        lib.zero_stats()
        lib.start_instrumentation()
        try:
            return __codspeed_root_frame__()
        finally:
            # Ensure instrumentation is stopped even if the test failed
            lib.stop_instrumentation()
            uri = get_git_relative_uri(nodeid, config.rootpath)
            lib.dump_stats_at(uri.encode("ascii"))
    finally:
        # Ensure GC is re-enabled even if the test failed
        if is_gc_enabled:
            gc.enable()


def wrap_runtest(
    lib: LibType,
    nodeid: str,
    config: pytest.Config,
    fn: Callable[P, T],
) -> Callable[P, T]:
    @functools.wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        return _run_with_instrumentation(lib, nodeid, config, fn, *args, **kwargs)

    return wrapped


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item | None):
    plugin = get_plugin(item.config)
    if not plugin.is_codspeed_enabled or not should_benchmark_item(item):
        # Defer to the default test protocol since no benchmarking is needed
        return None

    if has_benchmark_fixture(item):
        # Instrumentation is handled by the fixture
        return None

    plugin.benchmark_count += 1
    if not plugin.should_measure or not plugin.lib:
        # Benchmark counted but will be run in the default protocol
        return None

    # Wrap runtest and defer to default protocol
    item.runtest = wrap_runtest(plugin.lib, item.nodeid, item.config, item.runtest)
    return None


class BenchmarkFixture:
    """The fixture that can be used to benchmark a function."""

    def __init__(self, request: pytest.FixtureRequest):
        self.extra_info: dict = {}

        self._request = request

    def __call__(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        config = self._request.config
        plugin = get_plugin(config)
        plugin.benchmark_count += 1
        if plugin.is_codspeed_enabled and plugin.should_measure:
            assert plugin.lib is not None
            return _run_with_instrumentation(
                plugin.lib, self._request.node.nodeid, config, func, *args, **kwargs
            )
        else:
            return func(*args, **kwargs)


@pytest.fixture(scope="function")
def codspeed_benchmark(request: pytest.FixtureRequest) -> Callable:
    return BenchmarkFixture(request)


if not IS_PYTEST_BENCHMARK_INSTALLED:

    @pytest.fixture(scope="function")
    def benchmark(codspeed_benchmark, request: pytest.FixtureRequest):
        """
        Compatibility with pytest-benchmark
        """
        return codspeed_benchmark


@pytest.hookimpl()
def pytest_sessionfinish(session: pytest.Session, exitstatus):
    plugin = get_plugin(session.config)
    if plugin.is_codspeed_enabled:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        count_suffix = "benchmarked" if plugin.should_measure else "benchmark tested"
        reporter.write_sep(
            "=",
            f"{plugin.benchmark_count} {count_suffix}",
        )
