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
    result.stdout.fnmatch_lines(["*1 passed*"])
