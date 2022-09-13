import pytest


def test_plugin_disabled(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_some_addition_performance(benchmark):
            @benchmark
            def _():
                return 1 + 1
        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*1 passed*"])


def test_plugin_enabled(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_some_addition_performance(benchmark):
            @benchmark
            def _():
                return 1 + 1
        """
    )
    result = pytester.runpytest("--benchmark")
    result.stdout.fnmatch_lines(["*1 benchmarked*", "*1 passed*"])


def test_plugin_enabled_nothing_to_benchmark(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_some_addition_performance():
            return 1 + 1
        """
    )
    result = pytester.runpytest("--benchmark")
    result.stdout.fnmatch_lines(["*0 benchmarked*", "*1 passed*"])


def test_plugin_only_benchmark_collection(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.avalanche_benchmark
        def test_some_addition_performance():
            return 1 + 1

        @pytest.mark.abenchmark
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
    collection_result = pytester.runpytest("--only-benchmark", "--collect-only")
    collection_result.stdout.fnmatch_lines(
        [
            "*<Function test_some_addition_performance>*",
            "*<Function test_some_addition_performance_shorthand>*",
            "*<Function test_some_wrapped_benchmark>*",
            "*3/4 tests collected (1 deselected)*",
        ],
    )
