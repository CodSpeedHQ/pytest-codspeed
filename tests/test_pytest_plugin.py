import shutil
from contextlib import contextmanager

import pytest

VALGRIND_NOT_INSTALLED = shutil.which("valgrind") is None
skip_without_valgrind = pytest.mark.skipif(
    VALGRIND_NOT_INSTALLED, reason="valgrind not installed"
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


@skip_without_valgrind
def test_plugin_enabled_by_env(pytester: pytest.Pytester, codspeed_env) -> None:
    pytester.makepyfile(
        """
        def test_some_addition_performance(benchmark):
            @benchmark
            def _():
                return 1 + 1
        """
    )
    with codspeed_env():
        result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*1 benchmarked*", "*1 passed*"])


@skip_without_valgrind
def test_plugin_enabled_and_env(pytester: pytest.Pytester, codspeed_env) -> None:
    pytester.makepyfile(
        """
        def test_some_addition_performance(benchmark):
            @benchmark
            def _():
                return 1 + 1
        """
    )
    with codspeed_env():
        result = pytester.runpytest("--codspeed")
    result.stdout.fnmatch_lines(["*1 benchmarked*", "*1 passed*"])


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
