from __future__ import annotations

import contextlib
import functools
import gc
import os
import pkgutil
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest
from _pytest.fixtures import FixtureManager
from _pytest.runner import runtestprotocol

from pytest_codspeed.utils import get_git_relative_uri

from . import __version__
from ._wrapper import get_lib

if TYPE_CHECKING:
    from typing import Any, Callable, Iterator, ParamSpec, TypeVar

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


@contextlib.contextmanager
def collect_garbage() -> Iterator[None]:
    is_gc_enabled = gc.isenabled()
    if is_gc_enabled:
        gc.collect()
        gc.disable()

    try:
        yield
    finally:
        # Re-enable garbage collection if it was enabled previously
        if is_gc_enabled:
            gc.enable()


@contextlib.contextmanager
def prime_cache(
    item: pytest.Item | Callable[P, T],
    *args: Any,
    **kwargs: Any,
) -> Iterator[None]:
    if SUPPORTS_PERF_TRAMPOLINE:
        if isinstance(item, pytest.Item):
            runtestprotocol(item, *args, **kwargs)

            # Clear item's cached results
            _remove_cached_results_from_fixtures(item)
            _remove_setup_state_from_session(item)
        else:
            item(*args, **kwargs)

    yield


def _remove_cached_results_from_fixtures(item: pytest.Item) -> None:
    """Borrowed from pytest_rerunfailures._remove_cached_results_from_failed_fixtures"""
    fixtureinfo = getattr(item, "_fixtureinfo", None)
    name2fixturedefs = getattr(fixtureinfo, "name2fixturedefs", {})
    for fixture_defs in name2fixturedefs.values():
        for fixture_def in fixture_defs:
            setattr(fixture_def, "cached_result", None)


def _remove_setup_state_from_session(item: pytest.Item) -> None:
    """Borrowed from pytest_rerunfailures._remove_failed_setup_state_from_session"""
    item.session._setupstate.stack = {}


@contextlib.contextmanager
def add_instrumentation(
    lib: LibType,
    item: pytest.Item,
    inner_func: Callable[P, T] | None = None,
) -> Iterator[Callable[P, T]]:
    # Store original test function so we can restore it after instrumentation
    orig_obj: Callable[P, T] = item.obj

    # The test function to be run
    runtest: Callable[P, T] = inner_func or orig_obj

    # Wrap the test function with instrumentation
    @functools.wraps(runtest)
    def __codspeed_root_frame__(*args: P.args, **kwargs: P.kwargs) -> T:
        lib.zero_stats()
        lib.start_instrumentation()

        try:
            return runtest(*args, **kwargs)
        finally:
            lib.stop_instrumentation()
            uri = get_git_relative_uri(item.nodeid, item.config.rootpath)
            lib.dump_stats_at(uri.encode("ascii"))

    if not inner_func:
        item.obj = __codspeed_root_frame__

    try:
        yield __codspeed_root_frame__
    finally:
        # Restore unadorned function
        if not inner_func:
            item.obj = orig_obj


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(
    item: pytest.Item,
    nextitem: pytest.Item | None,
) -> bool | None:
    plugin = get_plugin(item.config)
    if not plugin.is_codspeed_enabled or not should_benchmark_item(item):
        return None  # Defer to default test protocol since no benchmarking is needed

    if has_benchmark_fixture(item):
        return None  # Instrumentation is handled by the fixture

    plugin.benchmark_count += 1
    if plugin.lib is None or not plugin.should_measure:
        return None  # Benchmark counted but will be run in the default protocol

    ihook = item.ihook
    ihook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)

    # Run the test
    with collect_garbage():
        # Run test (setup, call, and teardown) w/o logging, enabling logging will
        # increment passed/xfailed/failed counts resulting in inaccurate reporting
        with prime_cache(item, log=False, nextitem=nextitem):
            with add_instrumentation(plugin.lib, item):
                # Run test (setup, call, and teardown) w/ logging
                runtestprotocol(item, log=True, nextitem=nextitem)

    ihook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)
    return True


class BenchmarkFixture:
    """The fixture that can be used to benchmark a function."""

    def __init__(self, request: pytest.FixtureRequest):
        self.extra_info: dict = {}

        self._request = request

    def __call__(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        item = self._request._pyfuncitem
        plugin = get_plugin(item.config)
        plugin.benchmark_count += 1
        if (
            plugin.is_codspeed_enabled
            and plugin.lib is not None
            and plugin.should_measure
        ):
            with collect_garbage():
                # Run test (local) w/o instrumentation
                with prime_cache(func, *args, **kwargs):
                    with add_instrumentation(plugin.lib, item, func) as wrapped:
                        # Run test (local) w/ instrumentation
                        return wrapped(*args, **kwargs)
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
