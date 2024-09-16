from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from statistics import mean, median, stdev
from time import get_clock_info, perf_counter_ns
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

from pytest_codspeed.instruments import Instrument, MeasurementMode

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
    outlier_rounds: int
    iter_per_round: int
    warmup_iters: int

    @classmethod
    def from_list(
        cls, times: list[float], *, rounds: int, iter_per_round: int, warmup_iters: int
    ) -> BenchmarkStats:
        stdev_ns = stdev(times) if len(times) > 1 else 0
        mean_ns = mean(times)
        return cls(
            min_ns=min(times),
            max_ns=max(times),
            stdev_ns=stdev_ns,
            mean_ns=mean_ns,
            median_ns=median(times),
            rounds=rounds,
            outlier_rounds=sum(1 for t in times if abs(t - mean_ns) > stdev_ns),
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
    times: list[float] = []
    warmup_start = start = perf_counter_ns()
    while True:
        start = perf_counter_ns()
        fn(*args, **kwargs)
        end = perf_counter_ns()
        times.append(end - start)
        if end - warmup_start > config.warmup_time_ns:
            break

    # Round sizing
    warmup_mean_ns = mean(times)
    warmup_iters = len(times)
    times.clear()
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
        times.append(end - start)

        if end - run_start > config.max_time_ns:
            # TODO: log something
            break

    stats = BenchmarkStats.from_list(
        times, rounds=rounds, iter_per_round=iter_per_round, warmup_iters=warmup_iters
    )

    return Benchmark(name=name, uri=uri, config=config, stats=stats), out


class WallTimeInstrument(Instrument):
    instrument = MeasurementMode.WallTime

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
        reporter.write_sep(
            "=",
            f"{len(self.benchmarks)} benchmarked",
        )

        if len(self.benchmarks) == 0:
            return

        table = Table(title="Benchmark Results")

        table.add_column("Benchmark", justify="right", style="cyan", no_wrap=True)
        table.add_column("Time (best)", justify="right", style="green")
        table.add_column(
            "Rel. StdDev",
            justify="right",
        )
        table.add_column("Iter x Rounds", justify="right", style="blue")
        table.add_column("Outlier ratio", justify="right", style="blue")

        for bench in self.benchmarks:
            rsd = bench.stats.stdev_ns / bench.stats.mean_ns
            table.add_row(
                bench.name,
                f"{bench.stats.min_ns/bench.stats.iter_per_round:.2f}ns",
                f"{rsd*100:.1f}%",
                f"{bench.stats.iter_per_round} x {bench.stats.rounds}",
                f"{(bench.stats.outlier_rounds / bench.stats.rounds)*100:.1f}%",
            )

        console = Console()
        console.print(table)

    def get_result_dict(self) -> dict[str, Any]:
        return {
            "instrument": {
                "type": self.instrument.value,
                "clock_info": get_clock_info("perf_counter").__dict__,
            },
            "benchmarks": [asdict(bench) for bench in self.benchmarks],
        }
