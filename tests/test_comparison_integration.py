"""Integration tests for the local baseline comparison feature.

These tests verify the end-to-end behaviour of the comparison feature
as it appears in a real pytest session: two consecutive walltime runs in
the same working directory should produce a comparison report on the
second run.

Unit-level tests (BenchmarkDiff, compare_results, print_comparison_report)
live in test_comparison.py.
"""

import pytest
from conftest import run_pytest_codspeed_with_mode

from pytest_codspeed.instruments import MeasurementMode

# Minimal benchmark used across all tests.  sleep(0) is near-zero cost but
# forces the walltime instrument to produce a real benchmark entry with
# mean_ns in the JSON result.
_BENCH_FILE = """
import time

def test_trivial(benchmark):
    benchmark(lambda: time.sleep(0))
"""


class TestLocalComparison:
    def test_no_comparison_on_first_run(self, pytester: pytest.Pytester) -> None:
        """First run has no prior baseline — comparison section must not appear."""
        pytester.makepyfile(_BENCH_FILE)

        result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)

        result.assert_outcomes(passed=1)
        result.stdout.no_fnmatch_line("*CodSpeed local comparison*")

    def test_comparison_appears_on_second_run(self, pytester: pytest.Pytester) -> None:
        """Second run finds the first run's JSON and prints the comparison header."""
        pytester.makepyfile(_BENCH_FILE)

        # First run — writes .codspeed/results_xxx.json
        run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)

        # Second run — finds the first JSON as baseline
        result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)

        result.assert_outcomes(passed=1)
        result.stdout.fnmatch_lines(["*CodSpeed local comparison*"])

    def test_comparison_shows_benchmark_count(self, pytester: pytest.Pytester) -> None:
        """The footer line reports how many benchmarks were compared."""
        pytester.makepyfile(_BENCH_FILE)

        run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)
        result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)

        result.assert_outcomes(passed=1)
        result.stdout.fnmatch_lines(["*1 compared*"])

    def test_no_comparison_with_profile_folder(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When CODSPEED_PROFILE_FOLDER is set, comparison is skipped.

        The profile folder env var is used by the CodSpeed runner in CI; in
        that context the result file is written to a custom location and
        the local comparison loop makes no sense.
        """
        pytester.makepyfile(_BENCH_FILE)
        profile_dir = pytester.path / "profile"
        profile_dir.mkdir()
        (profile_dir / "results").mkdir()

        monkeypatch.setenv("CODSPEED_PROFILE_FOLDER", str(profile_dir))

        # First run with profile folder
        run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)
        # Second run with profile folder — still no comparison
        result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)

        result.assert_outcomes(passed=1)
        result.stdout.no_fnmatch_line("*CodSpeed local comparison*")

    def test_no_comparison_in_simulation_mode(self, pytester: pytest.Pytester) -> None:
        """Simulation mode does not produce mean_ns — comparison is silently skipped."""
        pytester.makepyfile(_BENCH_FILE)

        run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)

        # Second run in simulation mode — no benchmarks to compare
        result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.Simulation)

        result.assert_outcomes(passed=1)
        result.stdout.no_fnmatch_line("*CodSpeed local comparison*")
