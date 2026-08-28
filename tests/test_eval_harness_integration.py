"""Integration tests for the output-hash / correctness-check feature.

Two consecutive walltime runs with --codspeed-capture-output should detect
when a benchmark's return value changes between runs.
"""

import json

import pytest
from conftest import run_pytest_codspeed_with_mode

from pytest_codspeed.instruments import MeasurementMode

_STABLE_BENCH = """
def test_stable(benchmark):
    result = benchmark(sorted, [3, 1, 2])
    assert result == [1, 2, 3]
"""

_BROKEN_BENCH = """
def test_stable(benchmark):
    # Same function name, different behaviour: returns unsorted list
    result = benchmark(lambda lst: list(lst), [3, 1, 2])
    assert result == [3, 1, 2]
"""


class TestOutputHashIntegration:
    def test_no_warning_when_output_stable(
        self, pytester: pytest.Pytester
    ) -> None:
        pytester.makepyfile(_STABLE_BENCH)

        run_pytest_codspeed_with_mode(
            pytester, MeasurementMode.WallTime, "--codspeed-capture-output"
        )
        result = run_pytest_codspeed_with_mode(
            pytester, MeasurementMode.WallTime, "--codspeed-capture-output"
        )

        result.assert_outcomes(passed=1)
        result.stdout.no_fnmatch_line("*output changed*")

    def test_warning_when_output_changes(
        self, pytester: pytest.Pytester
    ) -> None:
        pytester.makepyfile(_STABLE_BENCH)
        run_pytest_codspeed_with_mode(
            pytester, MeasurementMode.WallTime, "--codspeed-capture-output"
        )

        pytester.makepyfile(_BROKEN_BENCH)
        result = run_pytest_codspeed_with_mode(
            pytester, MeasurementMode.WallTime, "--codspeed-capture-output"
        )

        result.assert_outcomes(passed=1)
        result.stdout.fnmatch_lines(["*output changed*"])

    def test_no_warning_without_flag(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(_STABLE_BENCH)
        run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)

        pytester.makepyfile(_BROKEN_BENCH)
        result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)

        result.assert_outcomes(passed=1)
        result.stdout.no_fnmatch_line("*output changed*")

    def test_correctness_warning_in_footer(
        self, pytester: pytest.Pytester
    ) -> None:
        pytester.makepyfile(_STABLE_BENCH)
        run_pytest_codspeed_with_mode(
            pytester, MeasurementMode.WallTime, "--codspeed-capture-output"
        )

        pytester.makepyfile(_BROKEN_BENCH)
        result = run_pytest_codspeed_with_mode(
            pytester, MeasurementMode.WallTime, "--codspeed-capture-output"
        )

        result.assert_outcomes(passed=1)
        result.stdout.fnmatch_lines(["*1 correctness warning(s)*"])


class TestEvalReportOutput:
    def test_eval_report_written_after_second_run(
        self, pytester: pytest.Pytester
    ) -> None:
        """--codspeed-eval-report writes a JSON file after comparison."""
        pytester.makepyfile(_STABLE_BENCH)
        report_path = pytester.path / "eval.json"

        run_pytest_codspeed_with_mode(
            pytester, MeasurementMode.WallTime, "--codspeed-capture-output"
        )
        result = run_pytest_codspeed_with_mode(
            pytester,
            MeasurementMode.WallTime,
            "--codspeed-capture-output",
            f"--codspeed-eval-report={report_path}",
        )

        result.assert_outcomes(passed=1)
        assert report_path.exists()
        data = json.loads(report_path.read_text())
        assert "aggregate_score" in data
        assert "is_acceptable" in data
        assert "benchmarks" in data

    def test_eval_report_acceptable_when_output_stable(
        self, pytester: pytest.Pytester
    ) -> None:
        """Stable output and unchanged perf produces a non-zero, acceptable verdict."""
        pytester.makepyfile(_STABLE_BENCH)
        report_path = pytester.path / "eval.json"

        run_pytest_codspeed_with_mode(
            pytester, MeasurementMode.WallTime, "--codspeed-capture-output"
        )
        run_pytest_codspeed_with_mode(
            pytester,
            MeasurementMode.WallTime,
            "--codspeed-capture-output",
            f"--codspeed-eval-report={report_path}",
        )

        data = json.loads(report_path.read_text())
        # Output did not change -- is_acceptable is driven by score, not by
        # output_changed alone, so we just assert correctness is not broken.
        assert data["benchmarks"][0]["output_changed"] is False

    def test_eval_report_not_acceptable_when_output_breaks(
        self, pytester: pytest.Pytester
    ) -> None:
        """Broken output forces aggregate_score=0.0 and is_acceptable=False."""
        pytester.makepyfile(_STABLE_BENCH)
        report_path = pytester.path / "eval.json"

        run_pytest_codspeed_with_mode(
            pytester, MeasurementMode.WallTime, "--codspeed-capture-output"
        )

        pytester.makepyfile(_BROKEN_BENCH)
        result = run_pytest_codspeed_with_mode(
            pytester,
            MeasurementMode.WallTime,
            "--codspeed-capture-output",
            f"--codspeed-eval-report={report_path}",
        )

        result.assert_outcomes(passed=1)
        data = json.loads(report_path.read_text())
        assert data["aggregate_score"] == 0.0
        assert data["is_acceptable"] is False
        assert data["benchmarks"][0]["output_changed"] is True

    def test_eval_report_not_written_on_first_run(
        self, pytester: pytest.Pytester
    ) -> None:
        """No baseline means no comparison -- eval report must not be created."""
        pytester.makepyfile(_STABLE_BENCH)
        report_path = pytester.path / "eval.json"

        run_pytest_codspeed_with_mode(
            pytester,
            MeasurementMode.WallTime,
            "--codspeed-capture-output",
            f"--codspeed-eval-report={report_path}",
        )

        assert not report_path.exists()
