from __future__ import annotations

import pytest
from conftest import (
    IS_PERF_TRAMPOLINE_SUPPORTED,
    MeasurementMode,
    run_pytest_codspeed_with_mode,
    skip_with_perf_trampoline,
    skip_without_pytest_benchmark,
    skip_without_valgrind,
)


@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_plugin_enabled_with_kwargs(
    pytester: pytest.Pytester, mode: MeasurementMode
) -> None:
    pytester.makepyfile(
        """
        def test_arg_kwarg_addition(benchmark):
            def fn(arg, kwarg=None):
                assert arg + kwarg == 40
            benchmark(fn, 25, kwarg=15)
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode)
    result.assert_outcomes(passed=1)


@skip_without_valgrind
@skip_with_perf_trampoline
def test_bench_enabled_header_without_perf(
    pytester: pytest.Pytester, codspeed_env
) -> None:
    pytester.copy_example("tests/examples/test_addition_fixture.py")
    with codspeed_env():
        result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        ["codspeed: * (enabled, mode: simulation, callgraph: not supported)"]
    )


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
    EXPECTED_OUTPUT_COUNT = 2 if IS_PERF_TRAMPOLINE_SUPPORTED else 1
    with codspeed_env():
        run_result = pytester.runpytest("--codspeed", "-s")
        print(run_result.stdout.str())
        assert run_result.outlines.count("I'm noisy marked!!!") == EXPECTED_OUTPUT_COUNT
        assert (
            run_result.outlines.count("I'm noisy fixtured!!!") == EXPECTED_OUTPUT_COUNT
        )


@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_plugin_enabled_and_env_bench_hierachy_called(
    pytester: pytest.Pytester, mode: MeasurementMode
) -> None:
    pytester.makepyfile(
        """
        import pytest
        import time

        class TestGroup:
            def setup_method(self):
                print(); print("Setup called")

            def teardown_method(self):
                print(); print("Teardown called")

            @pytest.mark.benchmark
            def test_child(self):
                time.sleep(0.1) # Avoids the test being too fast
                print(); print("Test called")

        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode, "-s")
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


@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_plugin_only_benchmark_collection(
    pytester: pytest.Pytester, mode: MeasurementMode
) -> None:
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
    collection_result = run_pytest_codspeed_with_mode(pytester, mode, "--collect-only")

    collection_result.stdout.fnmatch_lines_random(
        [
            "*<Function test_some_addition_performance>*",
            "*<Function test_some_addition_performance_shorthand>*",
            "*<Function test_some_wrapped_benchmark>*",
        ],
    )
    collection_result.assert_outcomes(
        deselected=1,
    )

    collection_result = run_pytest_codspeed_with_mode(
        pytester, mode, "--collect-only", "-k", "test_some_wrapped_benchmark"
    )
    collection_result.stdout.fnmatch_lines_random(
        [
            "*<Function test_some_wrapped_benchmark>*",
        ],
    )
    collection_result.assert_outcomes(
        deselected=3,
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
    result = pytester.runpytest(
        "--benchmark-only",
        "--benchmark-max-time=0",
        "--benchmark-warmup-iterations=1",
    )
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


def test_codspeed_marker_unexpected_args(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.codspeed_benchmark(
            "positional_arg"
        )
        def test_bench():
            pass
        """
    )
    result = pytester.runpytest("--codspeed")
    assert result.ret == 1
    result.stdout.fnmatch_lines_random(
        ["*ValueError: Positional arguments are not allowed in the benchmark marker*"],
    )


def test_codspeed_marker_unexpected_kwargs(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.codspeed_benchmark(
            not_allowed=True
        )
        def test_bench():
            pass
        """
    )
    result = pytester.runpytest("--codspeed")
    assert result.ret == 1
    result.stdout.fnmatch_lines_random(
        [
            "*ValueError: Unknown kwargs passed to benchmark marker: not_allowed*",
        ],
    )


def test_pytest_benchmark_extra_info(pytester: pytest.Pytester) -> None:
    """https://pytest-benchmark.readthedocs.io/en/latest/usage.html#extra-info"""
    pytester.makepyfile(
        """
        import time

        def test_my_stuff(benchmark):
            benchmark.extra_info['foo'] = 'bar'
            benchmark(time.sleep, 0.02)
        """
    )
    result = pytester.runpytest("--codspeed")
    assert result.ret == 0, "the run should have succeeded"


@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_pytest_benchmark_return_value(
    pytester: pytest.Pytester, mode: MeasurementMode
) -> None:
    pytester.makepyfile(
        """
        def calculate_something():
            return 1 + 1

        def test_my_stuff(benchmark):
            value = benchmark(calculate_something)
            assert value == 2
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode)
    assert result.ret == 0, "the run should have succeeded"


@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_print(pytester: pytest.Pytester, mode: MeasurementMode) -> None:
    """Test print statements are captured by pytest (i.e., not printed to terminal in
    the middle of the progress bar) and only displayed after test run (on failures)."""
    pytester.makepyfile(
        """
        import pytest, sys

        @pytest.mark.benchmark
        def test_print():
            print("print to stdout")
            print("print to stderr", file=sys.stderr)
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode)
    assert result.ret == 0, "the run should have succeeded"
    result.assert_outcomes(passed=1)
    result.stdout.no_fnmatch_line("*print to stdout*")
    result.stderr.no_fnmatch_line("*print to stderr*")


@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_capsys(pytester: pytest.Pytester, mode: MeasurementMode):
    """Test print statements are captured by capsys (i.e., not printed to terminal in
    the middle of the progress bar) and can be inspected within test."""
    pytester.makepyfile(
        """
        import pytest, sys

        @pytest.mark.benchmark
        def test_capsys(capsys):
            print("print to stdout")
            print("print to stderr", file=sys.stderr)

            stdout, stderr = capsys.readouterr()

            assert stdout == "print to stdout\\n"
            assert stderr == "print to stderr\\n"
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode)
    assert result.ret == 0, "the run should have succeeded"
    result.assert_outcomes(passed=1)
    result.stdout.no_fnmatch_line("*print to stdout*")
    result.stderr.no_fnmatch_line("*print to stderr*")


@pytest.mark.xfail(reason="not supported by pytest-benchmark, see #78")
@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_stateful_warmup_fixture(
    pytester: pytest.Pytester, mode: MeasurementMode
) -> None:
    """Test that the stateful warmup works correctly."""
    pytester.makepyfile(
        """
        import pytest

        def test_stateful_warmup(benchmark):
            has_run = False

            def b():
                nonlocal has_run
                assert not has_run, "Benchmark ran multiple times without setup"
                has_run = True

            benchmark(b)
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode)
    assert result.ret == 0, "the run should have succeeded"
    result.assert_outcomes(passed=1)


@pytest.mark.xfail(reason="not supported by pytest-benchmark, see #78")
@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_stateful_warmup_marker(
    pytester: pytest.Pytester, mode: MeasurementMode
) -> None:
    """Test that the stateful warmup marker works correctly."""
    pytester.makepyfile(
        """
        import pytest

        has_run = False

        @pytest.fixture(autouse=True)
        def fixture():
            global has_run
            has_run = False


        @pytest.mark.benchmark
        def test_stateful_warmup_marker():
            global has_run
            assert not has_run, "Benchmark ran multiple times without setup"
            has_run = True
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode)
    assert result.ret == 0, "the run should have succeeded"
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_benchmark_fixture_used_twice(
    pytester: pytest.Pytester, mode: MeasurementMode
) -> None:
    """Test that using the benchmark fixture twice in a test raises an error."""
    pytester.makepyfile(
        """
        def test_benchmark_used_twice(benchmark):
            def foo():
                pass

            benchmark(foo)
            benchmark(foo)
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode)
    assert result.ret == 1, "the run should have failed"
    result.stdout.fnmatch_lines(
        ["*RuntimeError: The benchmark fixture can only be used once per test*"]
    )


@pytest.mark.parametrize("mode", [*MeasurementMode])
def test_benchmark_fixture_used_normal_pedantic(
    pytester: pytest.Pytester, mode: MeasurementMode
) -> None:
    """Test that using the benchmark fixture twice in a test raises an error."""
    pytester.makepyfile(
        """
        def test_benchmark_used_twice(benchmark):
            def foo():
                pass

            benchmark(foo)
            benchmark.pedantic(foo)
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode)
    assert result.ret == 1, "the run should have failed"
    result.stdout.fnmatch_lines(
        ["*RuntimeError: The benchmark fixture can only be used once per test*"]
    )


ISOLATION_BENCH_COUNT = 3

ISOLATION_PID_FIXTURE = """
import os

import pytest


@pytest.mark.parametrize("index", range(3))
def test_bench(benchmark, index):
    benchmark(lambda: open("pids.txt", "a").write(f"{os.getpid()}\\n"))
"""


def run_isolation_subprocess(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    isolation: str | None = None,
) -> pytest.RunResult:
    # Children are real processes, so the parent must be one too.
    monkeypatch.setenv("CODSPEED_ENV", "1")
    monkeypatch.setenv("CODSPEED_RUNNER_MODE", "simulation")
    if isolation is None:
        monkeypatch.delenv("CODSPEED_PROCESS_ISOLATION", raising=False)
    else:
        monkeypatch.setenv("CODSPEED_PROCESS_ISOLATION", isolation)
    return pytester.runpytest_subprocess("--codspeed", "-p", "no:cacheprovider")


def read_pids(pytester: pytest.Pytester):
    return (pytester.path / "pids.txt").read_text().split()


def test_isolation_runs_each_benchmark_in_its_own_process(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytester.makepyfile(ISOLATION_PID_FIXTURE)
    result = run_isolation_subprocess(pytester, monkeypatch)
    assert result.ret == 0
    assert f"{ISOLATION_BENCH_COUNT} benchmarked" in result.stdout.str()
    pids = read_pids(pytester)
    # The body runs more than once per benchmark (warmup), so compare PIDs only.
    assert len(set(pids)) == ISOLATION_BENCH_COUNT


@pytest.mark.parametrize("value", ["0", "false"])
def test_isolation_disabled_shares_one_process(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    pytester.makepyfile(ISOLATION_PID_FIXTURE)
    result = run_isolation_subprocess(pytester, monkeypatch, value)
    assert result.ret == 0
    pids = read_pids(pytester)
    assert len(set(pids)) == 1


def test_isolation_parent_does_not_run_the_body(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytester.makepyfile(
        """
        def test_result(benchmark):
            result = benchmark(lambda: 42)
            assert result == 42
        """
    )
    result = run_isolation_subprocess(pytester, monkeypatch)
    assert result.ret == 0
    result.assert_outcomes(passed=1)


def test_isolation_failing_benchmark_fails_only_that_test(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytester.makepyfile(
        """
        def mark(name):
            with open("ran.txt", "a") as f:
                f.write(name + "\\n")

        def test_before(benchmark):
            benchmark(mark, "before")

        def test_raises(benchmark):
            def fn():
                raise ValueError("boom")
            benchmark(fn)

        def test_after(benchmark):
            benchmark(mark, "after")
        """
    )
    result = run_isolation_subprocess(pytester, monkeypatch)
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.assert_outcomes(passed=2, failed=1)
    result.stdout.fnmatch_lines(["*failed in its isolated process (exit code 1)*"])
    ran = set((pytester.path / "ran.txt").read_text().split())
    assert ran == {"before", "after"}


def test_isolation_invalid_env_value_errors(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytester.makepyfile(ISOLATION_PID_FIXTURE)
    result = run_isolation_subprocess(pytester, monkeypatch, "garbage")
    assert result.ret != 0
    result.stderr.fnmatch_lines(
        ["*CODSPEED_PROCESS_ISOLATION must be `true` or `false`, got `garbage`*"]
    )
