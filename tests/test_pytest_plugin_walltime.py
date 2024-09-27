import pytest
from conftest import run_pytest_codspeed_with_mode

from pytest_codspeed.instruments import MeasurementMode


def test_bench_enabled_header_with_perf(
    pytester: pytest.Pytester,
) -> None:
    pytester.copy_example("tests/examples/test_addition_fixture.py")
    result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)
    result.stdout.fnmatch_lines(["*test_some_addition_performance*", "*1 benchmarked*"])


def test_parametrization_naming(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import time, pytest

        @pytest.mark.parametrize("inp", ["toto", 12, 58.3])
        def test_my_stuff(benchmark, inp):
            benchmark(lambda: time.sleep(0.01))
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)
    # Make sure the parametrization is not broken
    print(result.outlines)
    result.stdout.fnmatch_lines_random(
        [
            "*test_my_stuff[[]toto[]]*",
            "*test_my_stuff[[]12[]]*",
            "*test_my_stuff[[]58.3[]]*",
            "*3 benchmarked*",
        ]
    )
