import os
from contextlib import contextmanager

import pytest
from conftest import (
    skip_with_perf_trampoline,
    skip_without_perf_trampoline,
    skip_without_pytest_benchmark,
    skip_without_valgrind,
)


@pytest.fixture(scope="function")
def codspeed_env(monkeypatch):
    @contextmanager
    def ctx_manager():
        monkeypatch.setenv("CODSPEED_ENV", "1")
        try:
            yield
        finally:
            monkeypatch.delenv("CODSPEED_ENV", raising=False)

    return ctx_manager


def test_plugin_enabled_without_env(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_some_addition_performance(benchmark):
            @benchmark
            def _():
                return 1 + 1
        """
    )
    result = pytester.runpytest("--codspeed")
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


def test_plugin_enabled_with_kwargs(pytester: pytest.Pytester, codspeed_env) -> None:
    pytester.makepyfile(
        """
        def test_arg_kwarg_addition(benchmark):
            def fn(arg, kwarg=None):
                assert arg + kwarg == 40
            benchmark(fn, 25, kwarg=15)
        """
    )
    result = pytester.runpytest("--codspeed")
    result.stdout.fnmatch_lines(["*1 benchmark tested*"])


@skip_without_valgrind
@skip_without_perf_trampoline
def test_bench_enabled_header_with_perf(
    pytester: pytest.Pytester, codspeed_env
) -> None:
    pytester.copy_example("tests/examples/test_addition_fixture.py")
    with codspeed_env():
        result = pytester.runpytest()
    result.stdout.fnmatch_lines(["codspeed: * (callgraph: enabled)"])


@skip_without_valgrind
@skip_with_perf_trampoline
def test_bench_enabled_header_without_perf(
    pytester: pytest.Pytester, codspeed_env
) -> None:
    pytester.copy_example("tests/examples/test_addition_fixture.py")
    with codspeed_env():
        result = pytester.runpytest()
    result.stdout.fnmatch_lines(["codspeed: * (callgraph: not supported)"])


@skip_without_valgrind
def test_plugin_enabled_by_env(pytester: pytest.Pytester, codspeed_env) -> None:
    pytester.copy_example("tests/examples/test_addition_fixture.py")
    with codspeed_env():
        result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*1 benchmarked*", "*1 passed*"])


@skip_without_valgrind
def test_plugin_enabled_and_env(pytester: pytest.Pytester, codspeed_env) -> None:
    pytester.copy_example("tests/examples/test_addition_fixture.py")
    with codspeed_env():
        result = pytester.runpytest("--codspeed")
    result.stdout.fnmatch_lines(["*1 benchmarked*", "*1 passed*"])


@skip_without_valgrind
def test_plugin_enabled_and_env_bench_run_once(
    pytester: pytest.Pytester, codspeed_env
) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.benchmark
        def test_noisy_bench_marked():
            print() # make sure noise is on its own line
            print("I'm noisy marked!!!")
            print()

        def test_noisy_bench_fxt(benchmark):
            @benchmark
            def _():
                print() # make sure noise is on its own line
                print("I'm noisy fixtured!!!")
                print()
        """
    )
    with codspeed_env():
        run_result = pytester.runpytest("--codspeed", "-s")
        print(run_result.stdout.str())
        assert run_result.outlines.count("I'm noisy marked!!!") == 1
        assert run_result.outlines.count("I'm noisy fixtured!!!") == 1


@skip_without_valgrind
def test_plugin_enabled_and_env_bench_hierachy_called(
    pytester: pytest.Pytester, codspeed_env
) -> None:
    pytester.makepyfile(
        """
        import pytest

        class TestGroup:
            def setup_method(self):
                print(); print("Setup called")

            def teardown(self):
                print(); print("Teardown called")

            @pytest.mark.benchmark
            def test_child(self):
                print(); print("Test called")

        """
    )
    with codspeed_env():
        result = pytester.runpytest("--codspeed", "-s")
        result.stdout.fnmatch_lines(
            [
                "Setup called",
                "Test called",
                "Teardown called",
            ]
        )


def test_plugin_disabled(pytester: pytest.Pytester) -> None:
    pytester.copy_example("tests/examples/test_addition_fixture.py")
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*1 passed*"])


@skip_without_valgrind
def test_plugin_enabled_nothing_to_benchmark(
    pytester: pytest.Pytester, codspeed_env
) -> None:
    pytester.makepyfile(
        """
        def test_some_addition_performance():
            return 1 + 1
        """
    )
    with codspeed_env():
        result = pytester.runpytest("--codspeed")
    result.stdout.fnmatch_lines(["*0 benchmarked*", "*1 deselected*"])


def test_plugin_only_benchmark_collection(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.codspeed_benchmark
        def test_some_addition_performance():
            return 1 + 1

        @pytest.mark.benchmark
        def test_some_addition_performance_shorthand():
            return 1 + 1

        def test_some_wrapped_benchmark(benchmark):
            @benchmark
            def _():
                hello = "hello"

        def test_another_useless_thing():
            assert True
        """
    )
    collection_result = pytester.runpytest("--codspeed", "--collect-only")
    collection_result.stdout.fnmatch_lines_random(
        [
            "*<Function test_some_addition_performance>*",
            "*<Function test_some_addition_performance_shorthand>*",
            "*<Function test_some_wrapped_benchmark>*",
            "*3/4 tests collected (1 deselected)*",
        ],
    )
    collection_result = pytester.runpytest(
        "--codspeed", "--collect-only", "-k", "test_some_wrapped_benchmark"
    )
    collection_result.stdout.fnmatch_lines_random(
        [
            "*<Function test_some_wrapped_benchmark>*",
            "*1/4 tests collected (3 deselected)*",
        ],
    )


@skip_without_pytest_benchmark
def test_pytest_benchmark_compatibility(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_some_wrapped_benchmark(benchmark):
            @benchmark
            def _():
                hello = "hello"
        """
    )
    result = pytester.runpytest("--benchmark-only")
    result.stdout.fnmatch_lines_random(
        [
            "*benchmark: 1 tests*",
            "*Name*",
            "*test_some_wrapped_benchmark*",
            "*Legend:*",
            "*Outliers:*",
            "*OPS: Operations Per Second*",
            "*Outliers:*",
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
            return 1 + 1

        def test_some_addition_fixtured(benchmark):
            @benchmark
            def fixtured_child():
                return 1 + 1
        """
    )
    with codspeed_env():
        result = pytester.runpytest("--codspeed")
    result.stdout.fnmatch_lines(["*2 benchmarked*", "*2 passed*"])
    current_pid = os.getpid()
    perf_filepath = f"/tmp/perf-{current_pid}.map"
    print(perf_filepath)

    with open(perf_filepath, "r") as perf_file:
        lines = perf_file.readlines()
        assert any(
            "py::_run_with_instrumentation.<locals>.__codspeed_root_frame__" in line
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
