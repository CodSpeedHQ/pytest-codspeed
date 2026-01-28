from __future__ import annotations

import os
import warnings
from dataclasses import asdict, dataclass
from math import ceil
from statistics import mean, quantiles, stdev
from time import get_clock_info, perf_counter_ns
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from pytest_codspeed import __semver_version__
from pytest_codspeed.instruments import Instrument
from pytest_codspeed.instruments.hooks import InstrumentHooks
from pytest_codspeed.utils import SUPPORTS_PERF_TRAMPOLINE

if TYPE_CHECKING:
    from typing import Any, Callable

    from pytest import Session

    from pytest_codspeed.config import PedanticOptions
    from pytest_codspeed.instruments import MeasurementMode, P, T
    from pytest_codspeed.plugin import BenchmarkMarkerOptions, CodSpeedConfig

DEFAULT_WARMUP_TIME_NS = 1_000_000_000
DEFAULT_MAX_TIME_NS = 3_000_000_000
TIMER_RESOLUTION_NS = get_clock_info("perf_counter").resolution * 1e9
DEFAULT_MIN_ROUND_TIME_NS = int(TIMER_RESOLUTION_NS * 1_000_000)

IQR_OUTLIER_FACTOR = 1.5
STDEV_OUTLIER_FACTOR = 3


@dataclass
class BenchmarkConfig:
    warmup_time_ns: int
    min_round_time_ns: float
    max_time_ns: int
    max_rounds: int | None

    @classmethod
    def from_codspeed_config_and_marker_data(
        cls, config: CodSpeedConfig, marker_data: BenchmarkMarkerOptions
    ) -> BenchmarkConfig:
        if marker_data.max_time is not None:
            max_time_ns = int(marker_data.max_time * 1e9)
        elif config.max_time_ns is not None:
            max_time_ns = config.max_time_ns
        else:
            max_time_ns = DEFAULT_MAX_TIME_NS

        if marker_data.max_rounds is not None:
            max_rounds = marker_data.max_rounds
        elif config.max_rounds is not None:
            max_rounds = config.max_rounds
        else:
            max_rounds = None

        if marker_data.min_time is not None:
            min_round_time_ns = int(marker_data.min_time * 1e9)
        else:
            min_round_time_ns = DEFAULT_MIN_ROUND_TIME_NS

        return cls(
            warmup_time_ns=config.warmup_time_ns
            if config.warmup_time_ns is not None
            else DEFAULT_WARMUP_TIME_NS,
            min_round_time_ns=min_round_time_ns,
            max_time_ns=max_time_ns,
            max_rounds=max_rounds,
        )


@dataclass
class BenchmarkStats:
    min_ns: float
    max_ns: float
    mean_ns: float
    stdev_ns: float

    q1_ns: float
    median_ns: float
    q3_ns: float

    rounds: int
    total_time: float
    iqr_outlier_rounds: int
    stdev_outlier_rounds: int
    iter_per_round: int
    warmup_iters: int

    @classmethod
    def from_list(
        cls,
        times_per_round_ns: list[float],
        *,
        rounds: int,
        iter_per_round: int,
        warmup_iters: int,
        total_time: float,
    ) -> BenchmarkStats:
        times_ns = [t / iter_per_round for t in times_per_round_ns]
        stdev_ns = stdev(times_ns) if len(times_ns) > 1 else 0
        mean_ns = mean(times_ns)
        if len(times_ns) > 1:
            q1_ns, median_ns, q3_ns = quantiles(times_ns, n=4)
        else:
            q1_ns, median_ns, q3_ns = (
                mean_ns,
                mean_ns,
                mean_ns,
            )
        iqr_ns = q3_ns - q1_ns
        iqr_outlier_rounds = sum(
            1
            for t in times_ns
            if t < q1_ns - IQR_OUTLIER_FACTOR * iqr_ns
            or t > q3_ns + IQR_OUTLIER_FACTOR * iqr_ns
        )
        stdev_outlier_rounds = sum(
            1
            for t in times_ns
            if t < mean_ns - STDEV_OUTLIER_FACTOR * stdev_ns
            or t > mean_ns + STDEV_OUTLIER_FACTOR * stdev_ns
        )

        return cls(
            min_ns=min(times_ns),
            max_ns=max(times_ns),
            stdev_ns=stdev_ns,
            mean_ns=mean_ns,
            q1_ns=q1_ns,
            median_ns=median_ns,
            q3_ns=q3_ns,
            rounds=rounds,
            total_time=total_time,
            iqr_outlier_rounds=iqr_outlier_rounds,
            stdev_outlier_rounds=stdev_outlier_rounds,
            iter_per_round=iter_per_round,
            warmup_iters=warmup_iters,
        )


@dataclass
class Benchmark:
    name: str
    uri: str

    config: BenchmarkConfig
    stats: BenchmarkStats


class WallTimeInstrument(Instrument):
    instrument = "walltime"
    instrument_hooks: InstrumentHooks | None

    def __init__(self, config: CodSpeedConfig, _mode: MeasurementMode) -> None:
        try:
            self.instrument_hooks = InstrumentHooks()
            self.instrument_hooks.set_integration("pytest-codspeed", __semver_version__)
        except RuntimeError as e:
            if os.environ.get("CODSPEED_ENV") is not None:
                warnings.warn(
                    f"Failed to initialize instrument hooks: {e}", RuntimeWarning
                )
            self.instrument_hooks = None

        self.config = config
        self.benchmarks: list[Benchmark] = []

    def get_instrument_config_str_and_warns(self) -> tuple[str, list[str]]:
        config_str = (
            f"mode: walltime, "
            f"callgraph: "
            f"{'enabled' if SUPPORTS_PERF_TRAMPOLINE else 'not supported'}, "
            f"timer_resolution: {TIMER_RESOLUTION_NS:.1f}ns"
        )
        return config_str, []

    def measure(
        self,
        marker_options: BenchmarkMarkerOptions,
        name: str,
        uri: str,
        fn: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        benchmark_config = BenchmarkConfig.from_codspeed_config_and_marker_data(
            self.config, marker_options
        )

        def __codspeed_root_frame__() -> T:
            return fn(*args, **kwargs)

        # Compute the actual result of the function
        out = __codspeed_root_frame__()

        # Warmup
        times_per_round_ns: list[float] = []
        warmup_start = start = perf_counter_ns()
        while True:
            start = perf_counter_ns()
            __codspeed_root_frame__()
            end = perf_counter_ns()
            times_per_round_ns.append(end - start)
            if end - warmup_start > benchmark_config.warmup_time_ns:
                break

        # Round sizing
        warmup_mean_ns = mean(times_per_round_ns)
        warmup_iters = len(times_per_round_ns)
        times_per_round_ns.clear()
        iter_per_round = (
            int(ceil(benchmark_config.min_round_time_ns / warmup_mean_ns))
            if warmup_mean_ns <= benchmark_config.min_round_time_ns
            else 1
        )
        if benchmark_config.max_rounds is None:
            round_time_ns = warmup_mean_ns * iter_per_round
            rounds = int(benchmark_config.max_time_ns / round_time_ns)
        else:
            rounds = benchmark_config.max_rounds
        rounds = max(1, rounds)

        # Benchmark
        iter_range = range(iter_per_round)
        run_start = perf_counter_ns()
        if self.instrument_hooks:
            self.instrument_hooks.start_benchmark()
        for _ in range(rounds):
            start = perf_counter_ns()
            for _ in iter_range:
                __codspeed_root_frame__()
            end = perf_counter_ns()
            times_per_round_ns.append(end - start)

            if end - run_start > benchmark_config.max_time_ns:
                # TODO: log something
                break
        if self.instrument_hooks:
            self.instrument_hooks.stop_benchmark()
            self.instrument_hooks.set_executed_benchmark(uri)
        benchmark_end = perf_counter_ns()
        total_time = (benchmark_end - run_start) / 1e9

        stats = BenchmarkStats.from_list(
            times_per_round_ns,
            rounds=rounds,
            total_time=total_time,
            iter_per_round=iter_per_round,
            warmup_iters=warmup_iters,
        )

        self.benchmarks.append(
            Benchmark(name=name, uri=uri, config=benchmark_config, stats=stats)
        )
        return out

    def measure_pedantic(  # noqa: C901
        self,
        marker_options: BenchmarkMarkerOptions,
        pedantic_options: PedanticOptions[T],
        name: str,
        uri: str,
    ) -> T:
        benchmark_config = BenchmarkConfig.from_codspeed_config_and_marker_data(
            self.config, marker_options
        )

        def __codspeed_root_frame__(*args, **kwargs) -> T:
            return pedantic_options.target(*args, **kwargs)

        iter_range = range(pedantic_options.iterations)

        # Warmup
        for _ in range(pedantic_options.warmup_rounds):
            args, kwargs = pedantic_options.setup_and_get_args_kwargs()
            for _ in iter_range:
                __codspeed_root_frame__(*args, **kwargs)
            if pedantic_options.teardown is not None:
                pedantic_options.teardown(*args, **kwargs)

        # Benchmark
        times_per_round_ns: list[float] = []
        benchmark_start = perf_counter_ns()
        if self.instrument_hooks:
            self.instrument_hooks.start_benchmark()
        for _ in range(pedantic_options.rounds):
            start = perf_counter_ns()
            args, kwargs = pedantic_options.setup_and_get_args_kwargs()
            for _ in iter_range:
                __codspeed_root_frame__(*args, **kwargs)
            end = perf_counter_ns()
            times_per_round_ns.append(end - start)
            if pedantic_options.teardown is not None:
                pedantic_options.teardown(*args, **kwargs)
        if self.instrument_hooks:
            self.instrument_hooks.stop_benchmark()
            self.instrument_hooks.set_executed_benchmark(uri)
        benchmark_end = perf_counter_ns()
        total_time = (benchmark_end - benchmark_start) / 1e9
        stats = BenchmarkStats.from_list(
            times_per_round_ns,
            rounds=pedantic_options.rounds,
            total_time=total_time,
            iter_per_round=pedantic_options.iterations,
            warmup_iters=pedantic_options.warmup_rounds,
        )

        # Compute the actual result of the function
        args, kwargs = pedantic_options.setup_and_get_args_kwargs()
        out = __codspeed_root_frame__(*args, **kwargs)
        if pedantic_options.teardown is not None:
            pedantic_options.teardown(*args, **kwargs)

        self.benchmarks.append(
            Benchmark(name=name, uri=uri, config=benchmark_config, stats=stats)
        )
        return out

    def report(self, session: Session) -> None:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        assert reporter is not None, "terminalreporter not found"

        if len(self.benchmarks) == 0:
            reporter.write_sep(
                "=",
                f"{len(self.benchmarks)} benchmarked",
            )
            return
        self._print_benchmark_table()
        reporter.write_sep(
            "=",
            f"{len(self.benchmarks)} benchmarked",
        )

    def _print_benchmark_table(self) -> None:
        table = Table(title="Benchmark Results")

        table.add_column("Benchmark", justify="right", style="cyan", no_wrap=True)
        table.add_column("Time (best)", justify="right", style="green bold")
        table.add_column(
            "Rel. StdDev",
            justify="right",
        )
        table.add_column("Run time", justify="right")
        table.add_column("Iters", justify="right")

        for bench in self.benchmarks:
            rsd = bench.stats.stdev_ns / bench.stats.mean_ns
            rsd_text = Text(f"{rsd * 100:.1f}%")
            if rsd > 0.1:
                rsd_text.stylize("red bold")
            table.add_row(
                escape(bench.name),
                format_time(bench.stats.min_ns / bench.stats.iter_per_round),
                rsd_text,
                f"{bench.stats.total_time:,.2f}s",
                f"{bench.stats.iter_per_round * bench.stats.rounds:,}",
            )

        console = Console()
        print("\n")
        console.print(table)

    def get_result_dict(self) -> dict[str, Any]:
        return {
            "instrument": {
                "type": self.instrument,
                "clock_info": get_clock_info("perf_counter").__dict__,
            },
            "benchmarks": [asdict(bench) for bench in self.benchmarks],
        }


def format_time(time_ns: float) -> str:
    """Format time in nanoseconds to a human-readable string with appropriate units.

    Args:
        time_ns: Time in nanoseconds

    Returns:
        Formatted string with appropriate unit (ns, µs, ms, or s)

    Examples:
        >>> format_time(123)
        '123ns'
        >>> format_time(1_234)
        '1.23µs'
        >>> format_time(76_126_625)
        '76.1ms'
        >>> format_time(2_500_000_000)
        '2.50s'
    """
    if time_ns < 1_000:
        # Less than 1 microsecond - show in nanoseconds
        return f"{time_ns:.0f}ns"
    elif time_ns < 1_000_000:
        # Less than 1 millisecond - show in microseconds
        return f"{time_ns / 1_000:.2f}µs"
    elif time_ns < 1_000_000_000:
        # Less than 1 second - show in milliseconds
        return f"{time_ns / 1_000_000:.1f}ms"
    else:
        # 1 second or more - show in seconds
        return f"{time_ns / 1_000_000_000:.2f}s"
