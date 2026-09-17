"""Unit tests for pytest_codspeed.comparison.

Tests are organised in three sections:
  - find_baseline  – file discovery logic
  - compare_results – diff classification logic
  - print_comparison_report – terminal output
"""

import json
import os
import time
from pathlib import Path

import pytest
from conftest import _bench, _make_result

from pytest_codspeed.comparison import (
    BenchmarkDiff,
    ComparisonReport,
    compare_results,
    find_baseline,
    print_comparison_report,
)

# ---------------------------------------------------------------------------
# find_baseline
# ---------------------------------------------------------------------------


class TestFindBaseline:
    def test_returns_none_for_empty_directory(self, tmp_path: Path) -> None:
        current = tmp_path / "results_1000.json"
        current.write_text("{}")
        # current is the only file; no baseline available
        assert find_baseline(tmp_path, current) is None

    def test_returns_none_when_no_results_files(self, tmp_path: Path) -> None:
        # Only non-matching files in the directory
        (tmp_path / "something_else.json").write_text("{}")
        current = tmp_path / "results_2000.json"
        current.write_text("{}")
        assert find_baseline(tmp_path, current) is None

    def test_returns_previous_file_when_one_exists(self, tmp_path: Path) -> None:
        older = tmp_path / "results_1000.json"
        older.write_text("{}")
        # Ensure mtime of older < mtime of current
        os.utime(older, (time.time() - 10, time.time() - 10))

        current = tmp_path / "results_2000.json"
        current.write_text("{}")

        assert find_baseline(tmp_path, current) == older

    def test_returns_most_recent_when_multiple_exist(self, tmp_path: Path) -> None:
        now = time.time()

        oldest = tmp_path / "results_1000.json"
        oldest.write_text("{}")
        os.utime(oldest, (now - 20, now - 20))

        middle = tmp_path / "results_2000.json"
        middle.write_text("{}")
        os.utime(middle, (now - 10, now - 10))

        current = tmp_path / "results_3000.json"
        current.write_text("{}")
        os.utime(current, (now, now))

        # Should return middle (most recent excluding current)
        assert find_baseline(tmp_path, current) == middle

    def test_ignores_current_path(self, tmp_path: Path) -> None:
        """find_baseline must never return the file we just wrote."""
        current = tmp_path / "results_9999.json"
        current.write_text("{}")
        assert find_baseline(tmp_path, current) is None


# ---------------------------------------------------------------------------
# compare_results
# ---------------------------------------------------------------------------


class TestCompareResults:
    def test_regression_detected(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path, "b.json", [_bench("mod::test_foo", 1_000_000)]
        )
        current = _make_result(
            tmp_path, "c.json", [_bench("mod::test_foo", 1_300_000)]
        )

        report = compare_results(baseline, current)

        assert len(report.regressions) == 1
        assert len(report.improvements) == 0
        assert len(report.unchanged) == 0
        diff = report.regressions[0]
        assert diff.name == "mod::test_foo"
        assert diff.is_regression is True
        assert diff.change_ratio == pytest.approx(0.3)

    def test_improvement_detected(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path, "b.json", [_bench("mod::test_foo", 1_000_000)]
        )
        current = _make_result(tmp_path, "c.json", [_bench("mod::test_foo", 700_000)])

        report = compare_results(baseline, current)

        assert len(report.improvements) == 1
        assert len(report.regressions) == 0
        diff = report.improvements[0]
        assert diff.is_improvement is True
        assert diff.change_ratio == pytest.approx(-0.3)

    def test_unchanged_below_threshold(self, tmp_path: Path) -> None:
        # 2 % change — below the 5 % threshold
        baseline = _make_result(
            tmp_path, "b.json", [_bench("mod::test_foo", 1_000_000)]
        )
        current = _make_result(
            tmp_path, "c.json", [_bench("mod::test_foo", 1_020_000)]
        )

        report = compare_results(baseline, current)

        assert len(report.unchanged) == 1
        assert len(report.regressions) == 0
        assert len(report.improvements) == 0

    def test_new_benchmark_detected(self, tmp_path: Path) -> None:
        baseline = _make_result(tmp_path, "b.json", [])
        current = _make_result(tmp_path, "c.json", [_bench("mod::test_new", 500_000)])

        report = compare_results(baseline, current)

        assert "mod::test_new" in report.new_benchmarks
        assert len(report.regressions) == 0

    def test_removed_benchmark_detected(self, tmp_path: Path) -> None:
        baseline = _make_result(tmp_path, "b.json", [_bench("mod::test_gone", 500_000)])
        current = _make_result(tmp_path, "c.json", [])

        report = compare_results(baseline, current)

        assert "mod::test_gone" in report.removed_benchmarks

    def test_multiple_benchmarks_classified_independently(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path,
            "b.json",
            [
                _bench("mod::test_fast", 1_000_000),
                _bench("mod::test_slow", 1_000_000),
                _bench("mod::test_ok", 1_000_000),
            ],
        )
        current = _make_result(
            tmp_path,
            "c.json",
            [
                _bench("mod::test_fast", 600_000),   # -40 % → improvement
                _bench("mod::test_slow", 1_500_000),  # +50 % → regression
                _bench("mod::test_ok", 1_010_000),   #  +1 % → unchanged
            ],
        )

        report = compare_results(baseline, current)

        assert len(report.regressions) == 1
        assert len(report.improvements) == 1
        assert len(report.unchanged) == 1

    def test_regressions_sorted_worst_first(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path,
            "b.json",
            [
                _bench("mod::test_a", 1_000_000),
                _bench("mod::test_b", 1_000_000),
            ],
        )
        current = _make_result(
            tmp_path,
            "c.json",
            [
                _bench("mod::test_a", 1_100_000),  # +10 %
                _bench("mod::test_b", 1_500_000),  # +50 %
            ],
        )
        report = compare_results(baseline, current)

        # Worst regression first
        assert report.regressions[0].name == "mod::test_b"
        assert report.regressions[1].name == "mod::test_a"

    def test_improvements_sorted_best_first(self, tmp_path: Path) -> None:
        baseline = _make_result(
            tmp_path,
            "b.json",
            [
                _bench("mod::test_a", 1_000_000),
                _bench("mod::test_b", 1_000_000),
            ],
        )
        current = _make_result(
            tmp_path,
            "c.json",
            [
                _bench("mod::test_a", 800_000),   # -20 %
                _bench("mod::test_b", 500_000),   # -50 %
            ],
        )
        report = compare_results(baseline, current)

        # Best improvement first (most negative change_ratio)
        assert report.improvements[0].name == "mod::test_b"
        assert report.improvements[1].name == "mod::test_a"

    def test_empty_benchmarks_returns_empty_report(self, tmp_path: Path) -> None:
        baseline = _make_result(tmp_path, "b.json", [])
        current = _make_result(tmp_path, "c.json", [])

        report = compare_results(baseline, current)

        assert report.total_compared == 0
        assert not report.has_changes

    def test_benchmarks_without_stats_are_ignored(self, tmp_path: Path) -> None:
        """Benchmarks missing stats.mean_ns must not crash the comparison."""
        baseline_path = tmp_path / "b.json"
        baseline_path.write_text(
            json.dumps(
                {
                    "benchmarks": [
                        {"uri": "mod::test_incomplete"},  # no stats key
                    ]
                }
            )
        )
        current = _make_result(tmp_path, "c.json", [_bench("mod::test_ok", 1_000_000)])

        report = compare_results(baseline_path, current)

        # test_incomplete has no stats → ignored; test_ok is new
        assert "mod::test_ok" in report.new_benchmarks


# ---------------------------------------------------------------------------
# print_comparison_report
# ---------------------------------------------------------------------------


class TestPrintComparisonReport:
    def _empty_report(self) -> ComparisonReport:
        return ComparisonReport(
            regressions=(),
            improvements=(),
            unchanged=(),
            new_benchmarks=(),
            removed_benchmarks=(),
        )

    def test_no_output_for_empty_report(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        baseline = tmp_path / "results_000.json"
        baseline.write_text("{}")

        print_comparison_report(self._empty_report(), baseline)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_regression_appears_in_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        baseline = tmp_path / "results_000.json"
        baseline.write_text("{}")
        diff = BenchmarkDiff(
            name="tests/test_foo.py::test_bench",
            baseline_mean_ns=1_000_000,
            current_mean_ns=1_500_000,
        )
        report = ComparisonReport(
            regressions=(diff,),
            improvements=(),
            unchanged=(),
            new_benchmarks=(),
            removed_benchmarks=(),
        )

        print_comparison_report(report, baseline)

        out = capsys.readouterr().out
        assert "Regressions" in out
        assert "test_bench" in out
        assert "+50.0%" in out

    def test_improvement_appears_in_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        baseline = tmp_path / "results_000.json"
        baseline.write_text("{}")
        diff = BenchmarkDiff(
            name="tests/test_foo.py::test_bench",
            baseline_mean_ns=1_000_000,
            current_mean_ns=600_000,
        )
        report = ComparisonReport(
            regressions=(),
            improvements=(diff,),
            unchanged=(),
            new_benchmarks=(),
            removed_benchmarks=(),
        )

        print_comparison_report(report, baseline)

        out = capsys.readouterr().out
        assert "Improvements" in out
        assert "test_bench" in out
        assert "-40.0%" in out

    def test_baseline_filename_shown_in_header(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        baseline = tmp_path / "results_12345.json"
        baseline.write_text("{}")
        diff = BenchmarkDiff(
            name="mod::test_x",
            baseline_mean_ns=1_000_000,
            current_mean_ns=1_200_000,
        )
        report = ComparisonReport(
            regressions=(diff,),
            improvements=(),
            unchanged=(),
            new_benchmarks=(),
            removed_benchmarks=(),
        )

        print_comparison_report(report, baseline)

        out = capsys.readouterr().out
        assert "results_12345.json" in out
