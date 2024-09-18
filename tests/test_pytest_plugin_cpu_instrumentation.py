import os

import pytest
from conftest import (
    run_pytest_codspeed_with_mode,
    skip_with_pytest_benchmark,
    skip_without_perf_trampoline,
    skip_without_pytest_xdist,
    skip_without_valgrind,
)

from pytest_codspeed.instruments import MeasurementMode


@skip_without_valgrind
@skip_without_perf_trampoline
def test_bench_enabled_header_with_perf(
    pytester: pytest.Pytester, codspeed_env
) -> None:
    pytester.copy_example("tests/examples/test_addition_fixture.py")
    with codspeed_env():
        result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        ["codspeed: * (enabled, mode: instrumentation, callgraph: enabled)"]
    )


def test_plugin_enabled_cpu_instrumentation_without_env(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        def test_some_addition_performance(benchmark):
            @benchmark
            def _():
                return 1 + 1
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, MeasurementMode.Instrumentation)
    result.stdout.fnmatch_lines(
        [
            (
                "*NOTICE: codspeed is enabled, but no "
                "performance measurement will be made*"
            ),
            "*1 benchmark tested*",
            "*1 passed*",
        ]
    )


@skip_without_valgrind
@skip_without_perf_trampoline
def test_perf_maps_generation(pytester: pytest.Pytester, codspeed_env) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.benchmark
        def test_some_addition_marked():
            assert 1 + 1

        def test_some_addition_fixtured(benchmark):
            @benchmark
            def fixtured_child():
                assert 1 + 1
        """
    )
    with codspeed_env():
        result = pytester.runpytest("--codspeed")
    result.stdout.fnmatch_lines(["*2 benchmarked*", "*2 passed*"])
    current_pid = os.getpid()
    perf_filepath = f"/tmp/perf-{current_pid}.map"
    print(perf_filepath)

    with open(perf_filepath) as perf_file:
        lines = perf_file.readlines()
        assert any(
            "py::ValgrindInstrument.measure.<locals>.__codspeed_root_frame__" in line
            for line in lines
        ), "No root frame found in perf map"
        assert any(
            "py::test_some_addition_marked" in line for line in lines
        ), "No marked test frame found in perf map"
        assert any(
            "py::test_some_addition_fixtured" in line for line in lines
        ), "No fixtured test frame found in perf map"
        assert any(
            "py::test_some_addition_fixtured.<locals>.fixtured_child" in line
            for line in lines
        ), "No fixtured child test frame found in perf map"


@skip_without_valgrind
@skip_with_pytest_benchmark
@skip_without_pytest_xdist
def test_pytest_xdist_concurrency_compatibility(
    pytester: pytest.Pytester, codspeed_env
) -> None:
    pytester.makepyfile(
        """
        import time, pytest

        def do_something():
            time.sleep(1)

        @pytest.mark.parametrize("i", range(256))
        def test_my_stuff(benchmark, i):
            benchmark(do_something)
        """
    )
    # Run the test multiple times to reduce the chance of a false positive
    ITERATIONS = 5
    for i in range(ITERATIONS):
        with codspeed_env():
            result = pytester.runpytest("--codspeed", "-n", "128")
        assert result.ret == 0, "the run should have succeeded"
        result.stdout.fnmatch_lines(["*256 passed*"])
