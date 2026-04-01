"""Unit tests for pytest_codspeed.eval_harness and output_changed in comparison."""

import json
import math
from pathlib import Path

import pytest

from pytest_codspeed.comparison import BenchmarkDiff, ComparisonReport, compare_results
from pytest_codspeed.eval_harness import EvalReport, compute_score


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(tmp_path: Path, filename: str, benchmarks: list) -> Path:
    path = tmp_path / filename
    path.write_text(
        json.dumps({"instrument": {"type": "walltime"}, "benchmarks": benchmarks})
    )
    return path


def _bench(uri: str, mean_ns: float, output_hash=None) -> dict:
    entry: dict = {"uri": uri, "stats": {"mean_ns": mean_ns}}
    if output_hash is not None:
        entry["output_hash"] = output_hash
    return entry


# ---------------------------------------------------------------------------
# compute_score
# ---------------------------------------------------------------------------


class TestComputeScore:
    def test_correct_improvement_returns_perf_gain(self) -> None:
        assert compute_score(0.33, output_changed=False) == pytest.approx(0.33)

    def test_correct_regression_returns_zero(self) -> None:
        assert compute_score(-0.20, output_changed=False) == 0.0

    def test_broken_output_always_zero(self) -> None:
        assert compute_score(0.50, output_changed=True) == 0.0

    def test_broken_output_zero_even_when_big_gain(self) -> None:
        assert compute_score(0.99, output_changed=True) == 0.0

    def test_unknown_correctness_returns_nan(self) -> None:
        assert math.isnan(compute_score(0.33, output_changed=None))

    def test_zero_gain_correct_returns_zero(self) -> None:
        assert compute_score(0.0, output_changed=False) == 0.0


# ---------------------------------------------------------------------------
# output_changed in compare_results
# ---------------------------------------------------------------------------


class TestOutputChanged:
    def test_same_hash_output_changed_false(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path, "b.json", [_bench("mod::test_foo", 1_000_000, "abc123")]
        )
        current = _make_result(
            tmp_path, "c.json", [_bench("mod::test_foo", 800_000, "abc123")]
        )
        report = compare_results(baseline, current)
        assert report.improvements[0].output_changed is False

    def test_different_hash_output_changed_true(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path, "b.json", [_bench("mod::test_foo", 1_000_000, "abc123")]
        )
        current = _make_result(
            tmp_path, "c.json", [_bench("mod::test_foo", 800_000, "xyz999")]
        )
        report = compare_results(baseline, current)
        assert report.improvements[0].output_changed is True

    def test_missing_hash_output_changed_none(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path, "b.json", [_bench("mod::test_foo", 1_000_000)]
        )
        current = _make_result(
            tmp_path, "c.json", [_bench("mod::test_foo", 800_000)]
        )
        report = compare_results(baseline, current)
        assert report.improvements[0].output_changed is None

    def test_partial_hash_output_changed_none(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path, "b.json", [_bench("mod::test_foo", 1_000_000, "abc123")]
        )
        current = _make_result(
            tmp_path, "c.json", [_bench("mod::test_foo", 800_000)]
        )
        report = compare_results(baseline, current)
        assert report.improvements[0].output_changed is None


# ---------------------------------------------------------------------------
# EvalReport
# ---------------------------------------------------------------------------


class TestEvalReport:
    def _report(self, output_changed, change_ratio: float) -> ComparisonReport:
        diff = BenchmarkDiff(
            name="mod::test_foo",
            baseline_mean_ns=1_000_000,
            current_mean_ns=1_000_000 * (1 + change_ratio),
            output_changed=output_changed,
        )
        if change_ratio > 0.05:
            return ComparisonReport(
                regressions=(diff,),
                improvements=(),
                unchanged=(),
                new_benchmarks=(),
                removed_benchmarks=(),
            )
        if change_ratio < -0.05:
            return ComparisonReport(
                regressions=(),
                improvements=(diff,),
                unchanged=(),
                new_benchmarks=(),
                removed_benchmarks=(),
            )
        return ComparisonReport(
            regressions=(),
            improvements=(),
            unchanged=(diff,),
            new_benchmarks=(),
            removed_benchmarks=(),
        )

    def test_acceptable_improvement_correct_output(self) -> None:
        report = self._report(output_changed=False, change_ratio=-0.30)
        eval_report = EvalReport.from_comparison(report)
        assert len(eval_report.acceptable) == 1
        assert len(eval_report.correctness_broken) == 0
        assert eval_report.entries[0].score == pytest.approx(0.30)

    def test_improvement_with_broken_output_not_acceptable(self) -> None:
        report = self._report(output_changed=True, change_ratio=-0.30)
        eval_report = EvalReport.from_comparison(report)
        assert len(eval_report.acceptable) == 0
        assert len(eval_report.correctness_broken) == 1
        assert eval_report.entries[0].score == 0.0

    def test_unknown_correctness_not_acceptable(self) -> None:
        report = self._report(output_changed=None, change_ratio=-0.30)
        eval_report = EvalReport.from_comparison(report)
        assert len(eval_report.acceptable) == 0
        assert len(eval_report.correctness_unknown) == 1
        assert math.isnan(eval_report.entries[0].score)

    def test_from_comparison_covers_all_buckets(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path,
            "b.json",
            [
                _bench("mod::test_fast", 1_000_000, "hash_a"),
                _bench("mod::test_slow", 1_000_000, "hash_b"),
                _bench("mod::test_ok", 1_000_000, "hash_c"),
            ],
        )
        current = _make_result(
            tmp_path,
            "c.json",
            [
                _bench("mod::test_fast", 600_000, "hash_a"),
                _bench("mod::test_slow", 1_500_000, "hash_x"),
                _bench("mod::test_ok", 1_010_000, "hash_c"),
            ],
        )
        comparison = compare_results(baseline, current)
        eval_report = EvalReport.from_comparison(comparison)

        assert len(eval_report.entries) == 3
        assert len(eval_report.acceptable) == 1
        assert len(eval_report.correctness_broken) == 1
