import pytest
from conftest import run_pytest_codspeed_with_mode

from pytest_codspeed.config import (
    BenchmarkMarkerOptions,
    CodSpeedConfig,
    PedanticOptions,
)
from pytest_codspeed.instruments.walltime import WallTimeInstrument
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


def test_benchmark_pedantic_walltime(
    pytester: pytest.Pytester,
) -> None:
    """Test that pedantic mode works with walltime mode."""
    pytester.makepyfile(
        """
        def test_pedantic_full_features(benchmark):
            setup_calls = 0
            teardown_calls = 0
            target_calls = 0

            def setup():
                nonlocal setup_calls
                setup_calls += 1
                return (1, 2), {"c": 3}

            def teardown(a, b, c):
                nonlocal teardown_calls
                teardown_calls += 1
                assert a == 1
                assert b == 2
                assert c == 3

            def target(a, b, c):
                nonlocal target_calls
                target_calls += 1
                assert a == 1
                assert b == 2
                assert c == 3
                return a + b + c

            result = benchmark.pedantic(
                target,
                setup=setup,
                teardown=teardown,
                rounds=3,
                warmup_rounds=1
            )

            # Verify the results
            assert result == 6  # 1 + 2 + 3
            assert setup_calls == 5  # 3 rounds + 1 warmup + 1 calibration
            assert teardown_calls == 5
            assert target_calls == 5
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.WallTime)
    assert result.ret == 0, "the run should have succeeded"
    result.assert_outcomes(passed=1)


def test_benchmark_pedantic_walltime_setup_not_timed(monkeypatch: pytest.MonkeyPatch):
    """Verify that the setup time is not included in the measurement when using pedantic mode with walltime."""
    current_time_ns = 0

    def fake_perf_counter_ns() -> int:
        return current_time_ns

    monkeypatch.setattr(
        "pytest_codspeed.instruments.walltime.perf_counter_ns", fake_perf_counter_ns
    )

    def setup() -> tuple[tuple[int], dict[str, int]]:
        nonlocal current_time_ns
        current_time_ns += 200
        return (1,), {"c": 2}

    def target(a: int, c: int) -> int:
        nonlocal current_time_ns
        current_time_ns += 400
        return a + c

    instrument = WallTimeInstrument(CodSpeedConfig(), MeasurementMode.WallTime)
    result = instrument.measure_pedantic(
        BenchmarkMarkerOptions(),
        PedanticOptions(
            target=target,
            setup=setup,
            teardown=None,
            rounds=2,
            warmup_rounds=0,
            iterations=1,
        ),
        name="test_pedantic_setup_not_timed",
        uri="tests/test_benchmark.py::test_pedantic_setup_not_timed",
    )

    assert result == 3
    assert len(instrument.benchmarks) == 1
    # Two rounds should each measure target-only time (400ns), excluding setup (200ns).
    assert instrument.benchmarks[0].stats.min_ns == 400
