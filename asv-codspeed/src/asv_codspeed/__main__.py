from __future__ import annotations

import argparse
import sys
from pathlib import Path

from asv_codspeed import __version__
from asv_codspeed.runner import run_benchmarks
from codspeed.instruments import MeasurementMode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="asv-codspeed",
        description="Run ASV benchmarks with CodSpeed instrumentation",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"asv-codspeed {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run ASV benchmarks")
    run_parser.add_argument(
        "benchmark_dir",
        type=Path,
        nargs="?",
        default=Path("benchmarks"),
        help="Path to benchmark directory (default: benchmarks/)",
    )
    run_parser.add_argument(
        "--mode",
        choices=[m.value for m in MeasurementMode],
        default=None,
        help="Measurement mode (default: walltime locally, simulation in CI)",
    )
    run_parser.add_argument(
        "--warmup-time",
        type=float,
        default=None,
        help="Warmup time in seconds (walltime mode only)",
    )
    run_parser.add_argument(
        "--max-time",
        type=float,
        default=None,
        help="Maximum benchmark time in seconds",
    )
    run_parser.add_argument(
        "--max-rounds",
        type=int,
        default=None,
        help="Maximum number of benchmark rounds",
    )
    run_parser.add_argument(
        "--bench",
        type=str,
        default=None,
        help="Regex pattern to filter benchmarks",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        import os

        # Determine mode
        if args.mode:
            mode = MeasurementMode(args.mode)
        elif os.environ.get("CODSPEED_ENV") is not None:
            if os.environ.get("CODSPEED_RUNNER_MODE") == "walltime":
                mode = MeasurementMode.WallTime
            else:
                mode = MeasurementMode.Simulation
        else:
            mode = MeasurementMode.WallTime

        profile_folder = os.environ.get("CODSPEED_PROFILE_FOLDER")

        return run_benchmarks(
            benchmark_dir=args.benchmark_dir,
            mode=mode,
            warmup_time=args.warmup_time,
            max_time=args.max_time,
            max_rounds=args.max_rounds,
            bench_filter=args.bench,
            profile_folder=Path(profile_folder) if profile_folder else None,
        )

    return 1


if __name__ == "__main__":
    sys.exit(main())
