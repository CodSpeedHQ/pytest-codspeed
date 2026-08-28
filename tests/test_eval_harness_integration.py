"""Integration tests for the output-hash / correctness-check feature.

Two consecutive walltime runs with --codspeed-capture-output should detect
when a benchmark's return value changes between runs.
"""

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
