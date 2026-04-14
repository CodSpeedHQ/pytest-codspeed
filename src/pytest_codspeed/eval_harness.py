"""Scoring utilities for evaluating LLM-generated optimisation suggestions.

After two consecutive walltime runs with ``--codspeed-capture-output``, the
local comparison report includes both a performance delta and a correctness
signal (``output_changed``).  This module turns those two signals into a
single scalar score that can be used to rank or accept/reject suggestions
automatically.

Score semantics
---------------
* ``1.0``  - 100 % faster, output unchanged (theoretical maximum).
* ``0.33`` - 33 % faster, output unchanged.
* ``0.0``  - any speedup, but output changed (correctness broken).
* ``nan``  - run was not collected with ``--codspeed-capture-output``;
             correctness is unknown, score cannot be computed.

Usage in an optimisation loop::

    from pytest_codspeed.comparison import compare_results
    from pytest_codspeed.eval_harness import compute_score, EvalReport

    report = compare_results(baseline_path, current_path)
    eval_report = EvalReport.from_comparison(report)
    for entry in eval_report.entries:
        print(entry.name, entry.score)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_codspeed.comparison import BenchmarkDiff, ComparisonReport


def compute_score(perf_gain: float, output_changed: bool | None) -> float:
    """Return a scalar quality score for a single optimisation suggestion.

    Args:
        perf_gain: Relative performance improvement, positive = faster.
                   Computed as ``-diff.change_ratio`` (so +0.33 means 33 %
                   faster).
        output_changed: ``True`` if the function's return value changed,
                        ``False`` if it stayed the same, ``None`` if the
                        capture flag was not used.

    Returns:
        * ``0.0`` when ``output_changed is True`` -- correctness is broken.
        * ``float('nan')`` when ``output_changed is None`` -- unknown.
        * ``max(0.0, perf_gain)`` otherwise -- reward speed, ignore slowdowns.
    """
    if output_changed is True:
        return 0.0
    if output_changed is None:
        return float("nan")
    return max(0.0, perf_gain)


@dataclass(frozen=True)
class EvalEntry:
    """Score for a single benchmark in an optimisation suggestion."""

    name: str
    perf_gain: float
    output_changed: bool | None
    score: float

    @property
    def is_acceptable(self) -> bool:
        """True when the suggestion improves perf without breaking correctness."""
        return not math.isnan(self.score) and self.score > 0.0

    @property
    def correctness_unknown(self) -> bool:
        return self.output_changed is None


@dataclass(frozen=True)
class EvalReport:
    """Aggregated evaluation of an optimisation suggestion across all benchmarks."""

    entries: tuple[EvalEntry, ...]

    @classmethod
    def from_comparison(cls, report: ComparisonReport) -> EvalReport:
        """Build an :class:`EvalReport` from a :class:`ComparisonReport`."""
        all_diffs: tuple[BenchmarkDiff, ...] = (
            *report.regressions,
            *report.improvements,
            *report.unchanged,
        )
        entries = tuple(
            EvalEntry(
                name=diff.name,
                perf_gain=-diff.change_ratio,
                output_changed=diff.output_changed,
                score=compute_score(-diff.change_ratio, diff.output_changed),
            )
            for diff in all_diffs
        )
        return cls(entries=entries)

    @property
    def acceptable(self) -> tuple[EvalEntry, ...]:
        return tuple(e for e in self.entries if e.is_acceptable)

    @property
    def correctness_broken(self) -> tuple[EvalEntry, ...]:
        return tuple(e for e in self.entries if e.output_changed is True)

    @property
    def correctness_unknown(self) -> tuple[EvalEntry, ...]:
        return tuple(e for e in self.entries if e.correctness_unknown)
