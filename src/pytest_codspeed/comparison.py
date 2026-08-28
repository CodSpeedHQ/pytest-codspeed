"""Local baseline comparison between consecutive CodSpeed runs.

Implements the feature planned in ``plugin.py``::

    # Storing the results will be later used for features such as
    # local comparison between runs.

Only walltime runs produce per-benchmark statistics (``mean_ns``).
Simulation/analysis runs do not include a ``benchmarks`` key in their
result JSON, so comparisons are silently skipped for those modes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

# A benchmark is considered regressed / improved only when the relative
# change exceeds these thresholds.  Below 5 % the measurement noise of a
# single local run is too high to draw reliable conclusions.
_REGRESSION_THRESHOLD = 0.05
_IMPROVEMENT_THRESHOLD = 0.05


# ---------------------------------------------------------------------------
# Public data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BenchmarkDiff:
    """Performance delta for a single benchmark between two runs."""

    name: str
    baseline_mean_ns: float
    current_mean_ns: float

    @property
    def change_ratio(self) -> float:
        """Signed relative change.

        Positive  → slower (regression).
        Negative  → faster (improvement).
        """
        return (self.current_mean_ns - self.baseline_mean_ns) / self.baseline_mean_ns

    @property
    def change_pct(self) -> str:
        sign = "+" if self.change_ratio >= 0 else ""
        return f"{sign}{self.change_ratio * 100:.1f}%"

    @property
    def is_regression(self) -> bool:
        return self.change_ratio > _REGRESSION_THRESHOLD

    @property
    def is_improvement(self) -> bool:
        return self.change_ratio < -_IMPROVEMENT_THRESHOLD


@dataclass(frozen=True)
class ComparisonReport:
    """Full comparison report between a baseline run and the current run."""

    regressions: tuple[BenchmarkDiff, ...]
    improvements: tuple[BenchmarkDiff, ...]
    unchanged: tuple[BenchmarkDiff, ...]
    new_benchmarks: tuple[str, ...]
    removed_benchmarks: tuple[str, ...]

    @property
    def has_changes(self) -> bool:
        return bool(
            self.regressions
            or self.improvements
            or self.new_benchmarks
            or self.removed_benchmarks
        )

    @property
    def total_compared(self) -> int:
        return len(self.regressions) + len(self.improvements) + len(self.unchanged)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def find_baseline(results_dir: Path, current_path: Path) -> Path | None:
    """Return the most recent ``results_*.json`` that is not *current_path*.

    Files are ranked by modification time (most recent first).  The filename
    itself encodes a millisecond timestamp (``results_{ms}.json``) so mtime
    and filename order are equivalent in practice; mtime is simpler to sort.

    Returns ``None`` when the directory contains no prior run.
    """
    candidates = sorted(
        (p for p in results_dir.glob("results_*.json") if p != current_path),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------


def _extract_benchmarks(data: dict[str, Any]) -> dict[str, float]:
    """Return ``{uri: mean_ns}`` from a parsed results JSON.

    Benchmarks without a ``stats.mean_ns`` field (e.g. simulation-mode
    stubs) are silently ignored.
    """
    result: dict[str, float] = {}
    for bench in data.get("benchmarks", []):
        stats = bench.get("stats") or {}
        mean_ns = stats.get("mean_ns")
        if mean_ns is not None:
            result[bench["uri"]] = float(mean_ns)
    return result


def compare_results(baseline_path: Path, current_path: Path) -> ComparisonReport:
    """Compare two CodSpeed result files and return a :class:`ComparisonReport`.

    Args:
        baseline_path: Path to the older ``results_*.json`` file.
        current_path:  Path to the newly written ``results_*.json`` file.

    Returns:
        A :class:`ComparisonReport` classifying every benchmark as regressed,
        improved, unchanged, new, or removed.
    """
    baseline = _extract_benchmarks(json.loads(baseline_path.read_text()))
    current = _extract_benchmarks(json.loads(current_path.read_text()))

    regressions: list[BenchmarkDiff] = []
    improvements: list[BenchmarkDiff] = []
    unchanged: list[BenchmarkDiff] = []
    new_benchmarks: list[str] = []

    for uri, current_mean in current.items():
        if uri not in baseline:
            new_benchmarks.append(uri)
            continue
        diff = BenchmarkDiff(
            name=uri,
            baseline_mean_ns=baseline[uri],
            current_mean_ns=current_mean,
        )
        if diff.is_regression:
            regressions.append(diff)
        elif diff.is_improvement:
            improvements.append(diff)
        else:
            unchanged.append(diff)

    removed_benchmarks = [uri for uri in baseline if uri not in current]

    return ComparisonReport(
        # Sort regressions worst-first, improvements best-first.
        regressions=tuple(
            sorted(regressions, key=lambda d: d.change_ratio, reverse=True)
        ),
        improvements=tuple(sorted(improvements, key=lambda d: d.change_ratio)),
        unchanged=tuple(unchanged),
        new_benchmarks=tuple(new_benchmarks),
        removed_benchmarks=tuple(removed_benchmarks),
    )


# ---------------------------------------------------------------------------
# Terminal output
# ---------------------------------------------------------------------------


def _format_ns(ns: float) -> str:
    """Format a nanosecond duration as a human-readable string."""
    if ns >= 1_000_000_000:
        return f"{ns / 1_000_000_000:.2f}s"
    if ns >= 1_000_000:
        return f"{ns / 1_000_000:.2f}ms"
    if ns >= 1_000:
        return f"{ns / 1_000:.2f}µs"
    return f"{ns:.0f}ns"


def _short_name(uri: str) -> str:
    """Return the test function name part of a benchmark URI."""
    return uri.split("::")[-1] if "::" in uri else uri


def print_comparison_report(report: ComparisonReport, baseline_path: Path) -> None:
    """Print a human-readable comparison report to stdout.

    Produces no output when no benchmarks were compared (e.g. simulation
    mode) to avoid polluting CI logs with empty sections.
    """
    if report.total_compared == 0 and not report.new_benchmarks:
        return

    print(f"\n  CodSpeed local comparison  (vs {baseline_path.name})")
    print("  " + "─" * 62)

    if report.regressions:
        print(f"\n  ✗  Regressions ({len(report.regressions)})")
        for diff in report.regressions:
            print(
                f"     {_short_name(diff.name):<42}"
                f"  {_format_ns(diff.baseline_mean_ns):>8}"
                f" → {_format_ns(diff.current_mean_ns):>8}"
                f"  {diff.change_pct}"
            )

    if report.improvements:
        print(f"\n  ✓  Improvements ({len(report.improvements)})")
        for diff in report.improvements:
            print(
                f"     {_short_name(diff.name):<42}"
                f"  {_format_ns(diff.baseline_mean_ns):>8}"
                f" → {_format_ns(diff.current_mean_ns):>8}"
                f"  {diff.change_pct}"
            )

    if report.new_benchmarks:
        print(f"\n  +  New ({len(report.new_benchmarks)})")
        for uri in report.new_benchmarks:
            print(f"     {_short_name(uri)}")

    if report.removed_benchmarks:
        print(f"\n  -  Removed ({len(report.removed_benchmarks)})")
        for uri in report.removed_benchmarks:
            print(f"     {_short_name(uri)}")

    print(
        f"\n  {report.total_compared} compared"
        f"  ·  {len(report.regressions)} regression(s)"
        f"  ·  {len(report.improvements)} improvement(s)"
    )
    print()
