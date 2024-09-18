from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from statistics import mean, median, stdev
from time import get_clock_info, perf_counter_ns
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.text import Text

from pytest_codspeed.instruments import Instrument

if TYPE_CHECKING:
    from typing import Any, Callable

    from pytest import Session

    from pytest_codspeed.instruments import P, T
    from pytest_codspeed.plugin import CodSpeedConfig

DEFAULT_WARMUP_TIME_NS = 1_000_000_000
DEFAULT_MAX_TIME_NS = 3_000_000_000
TIMER_RESOLUTION_NS = get_clock_info("perf_counter").resolution * 1e9
DEFAULT_MIN_ROUND_TIME_NS = TIMER_RESOLUTION_NS * 100


@dataclass
class BenchmarkConfig:
    warmup_time_ns: int
    min_round_time_ns: float
    max_time_ns: int
    max_rounds: int | None

    @classmethod
    def from_codspeed_config(cls, config: CodSpeedConfig) -> BenchmarkConfig:
        return cls(
            warmup_time_ns=config.warmup_time_ns
            if config.warmup_time_ns is not None
            else DEFAULT_WARMUP_TIME_NS,
            min_round_time_ns=DEFAULT_MIN_ROUND_TIME_NS,
            max_time_ns=DEFAULT_MAX_TIME_NS,
            max_rounds=config.max_rounds or None,
        )


@dataclass
class BenchmarkStats:
    min_ns: float
    max_ns: float
    stdev_ns: float
    mean_ns: float
    median_ns: float

    rounds: int
    total_time: float
    outlier_rounds: int
    iter_per_round: int
    warmup_iters: int

    @classmethod
    def from_list(
        cls,
        times_ns: list[float],
        *,
        rounds: int,
        iter_per_round: int,
        warmup_iters: int,
        total_time: float,
    ) -> BenchmarkStats:
        stdev_ns = stdev(times_ns) if len(times_ns) > 1 else 0
        mean_ns = mean(times_ns)
        return cls(
            min_ns=min(times_ns),
            max_ns=max(times_ns),
            stdev_ns=stdev_ns,
            mean_ns=mean_ns,
            median_ns=median(times_ns),
            rounds=rounds,
            total_time=total_time,
            outlier_rounds=sum(1 for t in times_ns if abs(t - mean_ns) > stdev_ns),
            iter_per_round=iter_per_round,
            warmup_iters=warmup_iters,
        )


@dataclass
class Benchmark:
    name: str
    uri: str

    config: BenchmarkConfig
    stats: BenchmarkStats


def run_benchmark(
    name: str, uri: str, fn: Callable[P, T], args, kwargs, config: BenchmarkConfig
) -> tuple[Benchmark, T]:
    # Compute the actual result of the function
    out = fn(*args, **kwargs)

    # Warmup
    times_ns: list[float] = []
    warmup_start = start = perf_counter_ns()
    while True:
        start = perf_counter_ns()
        fn(*args, **kwargs)
        end = perf_counter_ns()
        times_ns.append(end - start)
        if end - warmup_start > config.warmup_time_ns:
            break

    # Round sizing
    warmup_mean_ns = mean(times_ns)
    warmup_iters = len(times_ns)
    times_ns.clear()
    iter_per_round = (
        int(ceil(config.min_round_time_ns / warmup_mean_ns))
        if warmup_mean_ns <= config.min_round_time_ns
        else 1
    )
    if config.max_rounds is None:
        round_time_ns = warmup_mean_ns * iter_per_round
        rounds = int(config.max_time_ns / round_time_ns)
    else:
        rounds = config.max_rounds

    # Benchmark
    iter_range = range(iter_per_round)
    run_start = perf_counter_ns()
    for _ in range(rounds):
        start = perf_counter_ns()
        for _ in iter_range:
            fn(*args, **kwargs)
        end = perf_counter_ns()
        times_ns.append(end - start)

        if end - run_start > config.max_time_ns:
            # TODO: log something
            break
    benchmark_end = perf_counter_ns()
    total_time = (benchmark_end - run_start) / 1e9

    stats = BenchmarkStats.from_list(
        times_ns,
        rounds=rounds,
        total_time=total_time,
        iter_per_round=iter_per_round,
        warmup_iters=warmup_iters,
    )

    return Benchmark(name=name, uri=uri, config=config, stats=stats), out


class WallTimeInstrument(Instrument):
    instrument = "walltime"

    def __init__(self, config: CodSpeedConfig) -> None:
        self.config = config
        self.benchmarks: list[Benchmark] = []

    def get_instrument_config_str_and_warns(self) -> tuple[str, list[str]]:
        return f"mode: walltime, timer_resolution: {TIMER_RESOLUTION_NS:.1f}ns", []

    def measure(
        self,
        name: str,
        uri: str,
        fn: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        bench, out = run_benchmark(
            name=name,
            uri=uri,
            fn=fn,
            args=args,
            kwargs=kwargs,
            config=BenchmarkConfig.from_codspeed_config(self.config),
        )
        self.benchmarks.append(bench)
        return out

    def report(self, session: Session) -> None:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")

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
            rsd_text = Text(f"{rsd*100:.1f}%")
            if rsd > 0.1:
                rsd_text.stylize("red bold")
            table.add_row(
                bench.name,
                f"{bench.stats.min_ns/bench.stats.iter_per_round:,.0f}ns",
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
