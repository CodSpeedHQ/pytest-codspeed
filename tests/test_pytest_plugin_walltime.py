import pytest
from conftest import run_pytest_codspeed_with_mode

from pytest_codspeed.instruments import MeasurementMode


def test_bench_enabled_header_with_perf(
    pytester: pytest.Pytester,
) -> None:
    pytester.copy_example("tests/examples/test_addition_fixture.py")
    result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)
    result.stdout.fnmatch_lines(["*test_some_addition_performance*", "*1 benchmarked*"])
