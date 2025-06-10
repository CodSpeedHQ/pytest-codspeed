from __future__ import annotations

import functools
import gc
import json
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import TYPE_CHECKING

import pytest
from _pytest.fixtures import FixtureManager

from pytest_codspeed.config import (
    BenchmarkMarkerOptions,
    CodSpeedConfig,
    PedanticOptions,
)
from pytest_codspeed.instruments import MeasurementMode, get_instrument_from_mode
from pytest_codspeed.utils import (
    BEFORE_PYTEST_8_1_1,
    IS_PYTEST_BENCHMARK_INSTALLED,
    IS_PYTEST_SPEED_INSTALLED,
    get_environment_metadata,
    get_git_relative_uri_and_name,
)

from . import __version__

if TYPE_CHECKING:
    from typing import Any, Callable, TypeVar

    from pytest_codspeed.instruments import Instrument

    T = TypeVar("T")


@pytest.hookimpl(trylast=True)
def pytest_addoption(parser: pytest.Parser):
    group = parser.getgroup("CodSpeed benchmarking")
    group.addoption(
        "--codspeed",
        action="store_true",
        default=False,
        help="Enable codspeed (not required when using the CodSpeed action)",
    )
    group.addoption(
        "--codspeed-mode",
        action="store",
        choices=[mode.value for mode in MeasurementMode],
        help="The measurement tool to use for measuring performance",
    )
    group.addoption(
        "--codspeed-warmup-time",
        action="store",
        type=float,
        help=(
            "The time to warm up the benchmark for (in seconds), only for walltime mode"
        ),
    )
    group.addoption(
        "--codspeed-max-time",
        action="store",
        type=float,
        help=(
            "The maximum time to run a benchmark for (in seconds), "
            "only for walltime mode"
        ),
    )
    group.addoption(
        "--codspeed-max-rounds",
        action="store",
        type=int,
        help=(
            "The maximum number of rounds to run a benchmark for"
            ", only for walltime mode"
        ),
    )


@dataclass(unsafe_hash=True)
class CodSpeedPlugin:
    is_codspeed_enabled: bool
    mode: MeasurementMode
    instrument: Instrument
    config: CodSpeedConfig
    disabled_plugins: tuple[str, ...]
    profile_folder: Path | None
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

    if os.environ.get("CODSPEED_ENV") is not None:
        if os.environ.get("CODSPEED_RUNNER_MODE") == "walltime":
            default_mode = MeasurementMode.WallTime.value
        else:
            default_mode = MeasurementMode.Instrumentation.value
    else:
        default_mode = MeasurementMode.WallTime.value

    mode = MeasurementMode(config.getoption("--codspeed-mode", None) or default_mode)
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

    profile_folder = os.environ.get("CODSPEED_PROFILE_FOLDER")

    codspeed_config = CodSpeedConfig.from_pytest_config(config)

    plugin = CodSpeedPlugin(
        disabled_plugins=tuple(disabled_plugins),
        is_codspeed_enabled=is_codspeed_enabled,
        mode=mode,
        instrument=instrument(codspeed_config),
        config=codspeed_config,
        profile_folder=Path(profile_folder) if profile_folder else None,
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
    out = [
        (
            f"codspeed: {__version__} ("
            f"{'enabled' if plugin.is_codspeed_enabled else 'disabled'}, {config_str}"
            ")"
        ),
        *warns,
    ]
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
    node: pytest.Item,
    config: pytest.Config,
    pedantic_options: PedanticOptions | None,
    fn: Callable[..., T],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> T:
    marker_options = BenchmarkMarkerOptions.from_pytest_item(node)
    random.seed(0)
    is_gc_enabled = gc.isenabled()
    if is_gc_enabled:
        gc.collect()
        gc.disable()
    try:
        uri, name = get_git_relative_uri_and_name(node.nodeid, config.rootpath)
        if pedantic_options is None:
            return plugin.instrument.measure(
                marker_options, name, uri, fn, *args, **kwargs
            )
        else:
            return plugin.instrument.measure_pedantic(
                marker_options, pedantic_options, name, uri
            )
    finally:
        # Ensure GC is re-enabled even if the test failed
        if is_gc_enabled:
            gc.enable()


def wrap_runtest(
    plugin: CodSpeedPlugin,
    node: pytest.Item,
    config: pytest.Config,
    fn: Callable[..., T],
) -> Callable[..., T]:
    @functools.wraps(fn)
    def wrapped(*args: tuple, **kwargs: dict[str, Any]) -> T:
        return _measure(plugin, node, config, None, fn, args, kwargs)

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
    item.runtest = wrap_runtest(plugin, item, item.config, item.runtest)
    return None


@pytest.hookimpl()
def pytest_sessionfinish(session: pytest.Session, exitstatus):
    plugin = get_plugin(session.config)
    if plugin.is_codspeed_enabled:
        plugin.instrument.report(session)
        if plugin.profile_folder:
            result_path = plugin.profile_folder / "results" / f"{os.getpid()}.json"
        else:
            result_path = (
                session.config.rootpath / f".codspeed/results_{time() * 1000:.0f}.json"
            )
        data = {**get_environment_metadata(), **plugin.instrument.get_result_dict()}
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(data, indent=2))


class BenchmarkFixture:
    """The fixture that can be used to benchmark a function."""

    @property  # type: ignore
    def __class__(self):
        # Bypass the pytest-benchmark fixture class check
        # https://github.com/ionelmc/pytest-benchmark/commit/d6511e3474931feb4e862948128e0c389acfceec
        if IS_PYTEST_BENCHMARK_INSTALLED:
            from pytest_benchmark.fixture import (
                BenchmarkFixture as PytestBenchmarkFixture,
            )

            return PytestBenchmarkFixture
        return BenchmarkFixture

    def __init__(self, request: pytest.FixtureRequest):
        self.extra_info: dict = {}

        self._request = request
        self._config = self._request.config
        self._plugin = get_plugin(self._config)
        self._called = False

    def __call__(
        self, target: Callable[..., T], *args: tuple, **kwargs: dict[str, Any]
    ) -> T:
        if self._called:
            raise RuntimeError("The benchmark fixture can only be used once per test")
        self._called = True
        if self._plugin.is_codspeed_enabled:
            return _measure(
                self._plugin,
                self._request.node,
                self._config,
                None,
                target,
                args,
                kwargs,
            )
        else:
            return target(*args, **kwargs)

    def pedantic(
        self,
        target: Callable[..., T],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] = {},
        setup: Callable | None = None,
        teardown: Callable | None = None,
        rounds: int = 1,
        warmup_rounds: int = 0,
        iterations: int = 1,
    ):
        if self._called:
            raise RuntimeError("The benchmark fixture can only be used once per test")
        self._called = True
        pedantic_options = PedanticOptions(
            target=target,
            args=args,
            kwargs=kwargs,
            setup=setup,
            teardown=teardown,
            rounds=rounds,
            warmup_rounds=warmup_rounds,
            iterations=iterations,
        )
        if self._plugin.is_codspeed_enabled:
            return _measure(
                self._plugin,
                self._request.node,
                self._config,
                pedantic_options,
                target,
                args,
                kwargs,
            )
        else:
            args, kwargs = pedantic_options.setup_and_get_args_kwargs()
            result = target(*args, **kwargs)
            if pedantic_options.teardown is not None:
                pedantic_options.teardown(*args, **kwargs)
            return result


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
