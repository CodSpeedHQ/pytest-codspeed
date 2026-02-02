from __future__ import annotations

import gc
import json
import os
import random
from pathlib import Path
from time import time
from typing import TYPE_CHECKING, Any

from asv_codspeed.discovery import discover_benchmarks

from codspeed.config import BenchmarkMarkerOptions, CodSpeedConfig
from codspeed.instruments import MeasurementMode, get_instrument_from_mode
from codspeed.utils import get_environment_metadata, get_git_relative_path

if TYPE_CHECKING:
    from asv_codspeed.discovery import ASVBenchmark
    from codspeed.instruments import Instrument


def _get_uri(benchmark_name: str, benchmark_dir: Path) -> str:
    """Build a CodSpeed-compatible URI for a benchmark."""
    git_relative = get_git_relative_path(benchmark_dir.resolve())
    return f"{git_relative}::{benchmark_name}"


def run_benchmarks(
    benchmark_dir: Path,
    mode: MeasurementMode,
    warmup_time: float | None = None,
    max_time: float | None = None,
    max_rounds: int | None = None,
    bench_filter: str | None = None,
    profile_folder: Path | None = None,
) -> int:
    """Discover and run ASV benchmarks with CodSpeed instrumentation.

    Returns exit code (0 for success, 1 for failure).
    """
    from rich.console import Console

    console = Console()

    # Discover benchmarks
    benchmarks = discover_benchmarks(benchmark_dir, bench_filter)
    if not benchmarks:
        console.print("[yellow]No benchmarks found[/yellow]")
        return 1

    time_benchmarks = [b for b in benchmarks if b.type == "time"]
    if not time_benchmarks:
        console.print(
            "[yellow]No time benchmarks found (only time_* supported)[/yellow]"
        )
        return 1

    console.print(
        f"[bold]asv-codspeed[/bold]: {len(time_benchmarks)} time benchmark(s) found, "
        f"mode: {mode.value}"
    )

    # Build CodSpeed config
    codspeed_config = CodSpeedConfig(
        warmup_time_ns=(
            int(warmup_time * 1_000_000_000) if warmup_time is not None else None
        ),
        max_time_ns=int(max_time * 1_000_000_000) if max_time is not None else None,
        max_rounds=max_rounds,
    )

    # Create instrument, reporting as "pytest-codspeed" so the CodSpeed platform
    # treats results identically
    from codspeed import __semver_version__ as codspeed_version

    instrument_cls = get_instrument_from_mode(mode)
    instrument = instrument_cls(
        codspeed_config,
        integration_name="pytest-codspeed",
        integration_version=codspeed_version,
    )
    config_str, warns = instrument.get_instrument_config_str_and_warns()
    console.print(f"  {config_str}")
    for w in warns:
        console.print(f"  [yellow]{w}[/yellow]")

    # Run benchmarks
    marker_options = BenchmarkMarkerOptions()
    passed = 0
    failed = 0

    for bench in time_benchmarks:
        uri = _get_uri(bench.name, benchmark_dir)
        name = bench.name
        console.print(f"  Running: {name}...", end=" ")
        try:
            _run_single_benchmark(instrument, marker_options, bench, name, uri)
            console.print("[green]OK[/green]")
            passed += 1
        except Exception as e:
            console.print(f"[red]FAILED: {e}[/red]")
            failed += 1

    # Report results
    _report(console, instrument, mode, passed, failed)

    # Save results
    if profile_folder is None:
        profile_folder_env = os.environ.get("CODSPEED_PROFILE_FOLDER")
        if profile_folder_env:
            profile_folder = Path(profile_folder_env)

    if profile_folder:
        result_path = profile_folder / "results" / f"{os.getpid()}.json"
    else:
        result_path = benchmark_dir / f".codspeed/results_{time() * 1000:.0f}.json"

    data = {
        **get_environment_metadata("pytest-codspeed", codspeed_version),
        **instrument.get_result_dict(),
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(data, indent=2))
    console.print(f"Results saved to: {result_path}")

    return 1 if failed > 0 else 0


def _report(
    console: Any,
    instrument: Instrument,
    mode: MeasurementMode,
    passed: int,
    failed: int,
) -> None:
    """Print a summary report of benchmark results."""
    from codspeed.instruments.walltime import WallTimeInstrument

    if isinstance(instrument, WallTimeInstrument) and instrument.benchmarks:
        instrument.print_benchmark_table()

    total = passed + failed
    status = "passed" if failed == 0 else "with failures"
    console.print(f"\n[bold]===== {total} benchmarked ({passed} passed, {failed} failed) =====[/bold]")


def _run_single_benchmark(
    instrument: Instrument,
    marker_options: Any,
    bench: ASVBenchmark,
    name: str,
    uri: str,
) -> None:
    """Run a single ASV benchmark through the CodSpeed instrument."""
    # Setup
    if bench.setup is not None:
        if bench.params and bench.current_param_values:
            bench.setup(*bench.current_param_values)
        else:
            bench.setup()

    try:
        random.seed(0)
        is_gc_enabled = gc.isenabled()
        if is_gc_enabled:
            gc.collect()
            gc.disable()
        try:
            fn = bench.func
            if bench.params and bench.current_param_values:
                args = bench.current_param_values
            else:
                args = ()

            instrument.measure(marker_options, name, uri, fn, *args)
        finally:
            if is_gc_enabled:
                gc.enable()
    finally:
        # Teardown
        if bench.teardown is not None:
            if bench.params and bench.current_param_values:
                bench.teardown(*bench.current_param_values)
            else:
                bench.teardown()
