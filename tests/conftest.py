from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest

from pytest_codspeed.instruments import MeasurementMode
from pytest_codspeed.utils import IS_PYTEST_BENCHMARK_INSTALLED

if TYPE_CHECKING:
    from _pytest.pytester import RunResult

pytest_plugins = ["pytester"]

skip_without_pytest_benchmark = pytest.mark.skipif(
    not IS_PYTEST_BENCHMARK_INSTALLED, reason="pytest_benchmark not installed"
)
skip_with_pytest_benchmark = pytest.mark.skipif(
    IS_PYTEST_BENCHMARK_INSTALLED, reason="pytest_benchmark installed"
)
if IS_PYTEST_BENCHMARK_INSTALLED:
    pytest_plugins.append("pytest_benchmark")
    print(
        "NOTICE: Testing with pytest-benchmark compatibility",
        file=sys.stderr,
        flush=True,
    )

IS_VALGRIND_INSTALLED = shutil.which("valgrind") is not None
skip_without_valgrind = pytest.mark.skipif(
    "PYTEST_CODSPEED_FORCE_VALGRIND_TESTS" not in os.environ
    and not IS_VALGRIND_INSTALLED,
    reason="valgrind not installed",
)

if IS_VALGRIND_INSTALLED:
    print("NOTICE: Testing with valgrind compatibility", file=sys.stderr, flush=True)

IS_PERF_TRAMPOLINE_SUPPORTED = sys.version_info >= (3, 12)
skip_without_perf_trampoline = pytest.mark.skipif(
    not IS_PERF_TRAMPOLINE_SUPPORTED, reason="perf trampoline is not supported"
)

skip_with_perf_trampoline = pytest.mark.skipif(
    IS_PERF_TRAMPOLINE_SUPPORTED, reason="perf trampoline is supported"
)

# The name for the pytest-xdist plugin is just "xdist"
IS_PYTEST_XDIST_INSTALLED = importlib.util.find_spec("xdist") is not None
skip_without_pytest_xdist = pytest.mark.skipif(
    not IS_PYTEST_XDIST_INSTALLED,
    reason="pytest_xdist not installed",
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


def run_pytest_codspeed_with_mode(
    pytester: pytest.Pytester, mode: MeasurementMode, *args, **kwargs
) -> RunResult:
    csargs = [
        "--codspeed",
        f"--codspeed-mode={mode.value}",
    ]
    if mode == MeasurementMode.WallTime:
        # Run only 1 round to speed up the test times
        csargs.extend(["--codspeed-warmup-time=0", "--codspeed-max-rounds=2"])
    return pytester.runpytest(
        *csargs,
        *args,
        **kwargs,
    )
