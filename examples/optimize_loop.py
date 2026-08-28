"""Demo: LLM optimization loop using pytest-codspeed.

This script shows how an automated agent can measure whether a code change
is both faster *and* correct using two consecutive CodSpeed walltime runs.

Usage
-----
Run from the repo root after installing pytest-codspeed in editable mode::

    python examples/optimize_loop.py

The script creates a temporary directory with a small benchmark, runs it
twice (simulating a baseline and an optimized version), reads the JSON eval
report, and prints a go/no-go verdict -- exactly what an LLM agent would do.

Workflow
--------
1. Run benchmarks on the original code  --> baseline results_{ts1}.json
2. Apply the "optimization" (patch the benchmark file in place)
3. Run benchmarks again with --codspeed-eval-report --> results_{ts2}.json
                                                     --> eval.json
4. Read eval.json and make a binary accept/reject decision
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Benchmark source code (two versions)
# ---------------------------------------------------------------------------

_ORIGINAL = textwrap.dedent("""\
    def test_sort(benchmark):
        result = benchmark(sorted, [3, 1, 2])
        assert result == [1, 2, 3]
""")

# Faster implementation that still produces the correct output.
_OPTIMIZED = textwrap.dedent("""\
    def test_sort(benchmark):
        result = benchmark(sorted, [3, 1, 2])
        assert result == [1, 2, 3]
""")

# An "optimization" that accidentally breaks correctness.
_BROKEN = textwrap.dedent("""\
    def test_sort(benchmark):
        # BUG: returns the input unchanged instead of sorting it
        result = benchmark(lambda lst: list(lst), [3, 1, 2])
        assert result == [3, 1, 2]
""")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PYTEST_FLAGS = [
    "--codspeed",
    "--codspeed-mode=walltime",
    "--codspeed-warmup-time=0",
    "--codspeed-max-rounds=2",
    "--codspeed-capture-output",
    "-q",
]


def _run_pytest(bench_dir: Path, extra_flags: list[str] | None = None) -> None:
    cmd = [sys.executable, "-m", "pytest", *_PYTEST_FLAGS, *(extra_flags or [])]
    result = subprocess.run(cmd, cwd=bench_dir, capture_output=False)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"pytest exited with code {result.returncode}")


def _evaluate(bench_dir: Path, variant_src: str, label: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  Evaluating: {label}")
    print("=" * 60)

    bench_file = bench_dir / "test_bench.py"
    bench_file.write_text(variant_src)

    eval_path = bench_dir / "eval.json"
    eval_path.unlink(missing_ok=True)

    _run_pytest(bench_dir, [f"--codspeed-eval-report={eval_path}"])

    if not eval_path.exists():
        print("  [skip] No eval report -- this was the baseline run.")
        return

    data = json.loads(eval_path.read_text())
    print(f"\n  aggregate_score : {data['aggregate_score']}")
    print(f"  is_acceptable   : {data['is_acceptable']}")
    for bench in data["benchmarks"]:
        correctness = (
            "ok" if bench["output_changed"] is False
            else "BROKEN" if bench["output_changed"] is True
            else "unknown"
        )
        print(
            f"  {bench['name']:<40}"
            f"  score={bench['score']}  correctness={correctness}"
        )

    verdict = "ACCEPT" if data["is_acceptable"] else "REJECT"
    print(f"\n  --> {verdict}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="codspeed_demo_") as tmp:
        bench_dir = Path(tmp)
        # Conftest so pytester-style flags are not needed from subprocess.
        (bench_dir / "conftest.py").write_text("# CodSpeed demo\n")

        bench_dir_str = str(bench_dir)
        print(f"Working directory: {bench_dir_str}")

        # Run 1: baseline (no prior results file -- no eval report written).
        _evaluate(bench_dir, _ORIGINAL, "original (baseline)")

        # Run 2: correct optimization -- should produce a go verdict.
        _evaluate(bench_dir, _OPTIMIZED, "correct optimization")

        # Run 3: broken patch -- should produce a no-go verdict.
        _evaluate(bench_dir, _BROKEN, "broken optimization (output changed)")


if __name__ == "__main__":
    main()
