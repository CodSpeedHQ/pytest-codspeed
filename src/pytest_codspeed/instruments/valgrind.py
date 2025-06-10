from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from pytest_codspeed import __semver_version__
from pytest_codspeed.instruments import Instrument
from pytest_codspeed.instruments.hooks import InstrumentHooks
from pytest_codspeed.utils import SUPPORTS_PERF_TRAMPOLINE

if TYPE_CHECKING:
    from typing import Any, Callable

    from pytest import Session

    from pytest_codspeed.config import PedanticOptions
    from pytest_codspeed.instruments import T
    from pytest_codspeed.plugin import BenchmarkMarkerOptions, CodSpeedConfig


class ValgrindInstrument(Instrument):
    instrument = "valgrind"
    instrument_hooks: InstrumentHooks | None

    def __init__(self, config: CodSpeedConfig) -> None:
        self.benchmark_count = 0
        try:
            self.instrument_hooks = InstrumentHooks()
            self.instrument_hooks.set_integration("pytest-codspeed", __semver_version__)
        except RuntimeError:
            self.instrument_hooks = None

        self.should_measure = self.instrument_hooks is not None

    def get_instrument_config_str_and_warns(self) -> tuple[str, list[str]]:
        config = (
            f"mode: instrumentation, "
            f"callgraph: {'enabled' if SUPPORTS_PERF_TRAMPOLINE else 'not supported'}"
        )
        warnings = []
        if not self.should_measure:
            warnings.append(
                "\033[1m"
                "NOTICE: codspeed is enabled, but no performance measurement"
                " will be made since it's running in an unknown environment."
                "\033[0m"
            )
        return config, warnings

    def measure(
        self,
        marker_options: BenchmarkMarkerOptions,
        name: str,
        uri: str,
        fn: Callable[..., T],
        *args: tuple,
        **kwargs: dict[str, Any],
    ) -> T:
        self.benchmark_count += 1

        if not self.instrument_hooks:
            return fn(*args, **kwargs)

        def __codspeed_root_frame__() -> T:
            return fn(*args, **kwargs)

        if SUPPORTS_PERF_TRAMPOLINE:
            # Warmup CPython performance map cache
            __codspeed_root_frame__()

        # Manually call the library function to avoid an extra stack frame. Also
        # call the callgrind markers directly to avoid extra overhead.
        self.instrument_hooks.lib.callgrind_start_instrumentation()
        try:
            return __codspeed_root_frame__()
        finally:
            # Ensure instrumentation is stopped even if the test failed
            self.instrument_hooks.lib.callgrind_stop_instrumentation()
            self.instrument_hooks.set_executed_benchmark(uri)

    def measure_pedantic(
        self,
        marker_options: BenchmarkMarkerOptions,
        pedantic_options: PedanticOptions[T],
        name: str,
        uri: str,
    ) -> T:
        if pedantic_options.rounds != 1 or pedantic_options.iterations != 1:
            warnings.warn(
                "Valgrind instrument ignores rounds and iterations settings "
                "in pedantic mode"
            )
        if not self.instrument_hooks:
            args, kwargs = pedantic_options.setup_and_get_args_kwargs()
            out = pedantic_options.target(*args, **kwargs)
            if pedantic_options.teardown is not None:
                pedantic_options.teardown(*args, **kwargs)
            return out

        def __codspeed_root_frame__(*args, **kwargs) -> T:
            return pedantic_options.target(*args, **kwargs)

        # Warmup
        warmup_rounds = max(
            pedantic_options.warmup_rounds, 1 if SUPPORTS_PERF_TRAMPOLINE else 0
        )
        for _ in range(warmup_rounds):
            args, kwargs = pedantic_options.setup_and_get_args_kwargs()
            __codspeed_root_frame__(*args, **kwargs)
            if pedantic_options.teardown is not None:
                pedantic_options.teardown(*args, **kwargs)

        # Compute the actual result of the function
        args, kwargs = pedantic_options.setup_and_get_args_kwargs()
        self.instrument_hooks.lib.callgrind_start_instrumentation()
        try:
            out = __codspeed_root_frame__(*args, **kwargs)
        finally:
            self.instrument_hooks.lib.callgrind_stop_instrumentation()
            self.instrument_hooks.set_executed_benchmark(uri)
            if pedantic_options.teardown is not None:
                pedantic_options.teardown(*args, **kwargs)

        return out

    def report(self, session: Session) -> None:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        assert reporter is not None, "terminalreporter not found"
        count_suffix = "benchmarked" if self.should_measure else "benchmark tested"
        reporter.write_sep(
            "=",
            f"{self.benchmark_count} {count_suffix}",
        )

    def get_result_dict(self) -> dict[str, Any]:
        return {
            "instrument": {"type": self.instrument},
            # bench results will be dumped by valgrind
        }
