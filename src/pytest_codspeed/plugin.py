from __future__ import annotations

import functools
import gc
import importlib.util
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest
from _pytest.fixtures import FixtureManager

from pytest_codspeed.instruments import (
    CodSpeedMeasurementMode,
    get_instrument_from_mode,
)
from pytest_codspeed.utils import get_git_relative_uri_and_name

from . import __version__

if TYPE_CHECKING:
    from typing import Callable, ParamSpec, TypeVar

    from pytest_codspeed.instruments import Instrument

    T = TypeVar("T")
    P = ParamSpec("P")

IS_PYTEST_BENCHMARK_INSTALLED = importlib.util.find_spec("pytest_benchmark") is not None
IS_PYTEST_SPEED_INSTALLED = importlib.util.find_spec("pytest_speed") is not None
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
    mode: CodSpeedMeasurementMode
    instrument: Instrument
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
    mode = CodSpeedMeasurementMode.Instrumentation
    instrument = get_instrument_from_mode(mode)
    disabled_plugins: list[str] = []
    if is_codspeed_enabled:
        if IS_PYTEST_BENCHMARK_INSTALLED:
            # Disable pytest-benchmark
            object.__setattr__(config.option, "benchmark_disable", True)
            config.pluginmanager.set_blocked("pytest_benchmark")
            config.pluginmanager.set_blocked("pytest-benchmark")
            disabled_plugins.append("pytest-benchmark")
        if IS_PYTEST_SPEED_INSTALLED:
            # Disable pytest-speed
            config.pluginmanager.set_blocked("speed")
            disabled_plugins.append("pytest-speed")

    plugin = CodSpeedPlugin(
        disabled_plugins=tuple(disabled_plugins),
        is_codspeed_enabled=is_codspeed_enabled,
        mode=mode,
        instrument=instrument(),
    )
    config.pluginmanager.register(plugin, PLUGIN_NAME)


@pytest.hookimpl()
def pytest_plugin_registered(plugin, manager: pytest.PytestPluginManager):
    """
    Patch the benchmark fixture to use the codspeed one if codspeed is enabled and an
    alternative benchmark fixture is available
    """
    if (IS_PYTEST_BENCHMARK_INSTALLED or IS_PYTEST_SPEED_INSTALLED) and isinstance(
        plugin, FixtureManager
    ):
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
            # Archive the alternative benchmark fixture
            fixture_manager._arg2fixturedefs["__benchmark"] = (
                fixture_manager._arg2fixturedefs["benchmark"]
            )
            # Replace the alternative fixture with the codspeed one
            fixture_manager._arg2fixturedefs["benchmark"] = codspeed_benchmark_fixtures


@pytest.hookimpl(trylast=True)
def pytest_report_header(config: pytest.Config):
    plugin = get_plugin(config)
    config_str, warns = plugin.instrument.get_instrument_config_str_and_warns()
    out = [f"codspeed: {__version__} ({config_str})", *warns]
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


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
):
    """Filter out items that should not be benchmarked when codspeed is enabled"""
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


def _measure(
    plugin: CodSpeedPlugin,
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
    try:
        uri, name = get_git_relative_uri_and_name(nodeid, config.rootpath)
        return plugin.instrument.measure(name, uri, fn, *args, **kwargs)
    finally:
        # Ensure GC is re-enabled even if the test failed
        if is_gc_enabled:
            gc.enable()


def wrap_runtest(
    plugin: CodSpeedPlugin,
    nodeid: str,
    config: pytest.Config,
    fn: Callable[P, T],
) -> Callable[P, T]:
    @functools.wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        return _measure(plugin, nodeid, config, fn, *args, **kwargs)

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

    # Wrap runtest and defer to default protocol
    item.runtest = wrap_runtest(plugin, item.nodeid, item.config, item.runtest)
    return None


@pytest.hookimpl()
def pytest_sessionfinish(session: pytest.Session, exitstatus):
    plugin = get_plugin(session.config)
    if plugin.is_codspeed_enabled:
        plugin.instrument.report(session)


class BenchmarkFixture:
    """The fixture that can be used to benchmark a function."""

    def __init__(self, request: pytest.FixtureRequest):
        self.extra_info: dict = {}

        self._request = request

    def __call__(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        config = self._request.config
        plugin = get_plugin(config)
        if plugin.is_codspeed_enabled:
            return _measure(
                plugin, self._request.node.nodeid, config, func, *args, **kwargs
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
