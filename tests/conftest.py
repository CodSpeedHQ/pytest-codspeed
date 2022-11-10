import pkgutil
import shutil
import sys

import pytest

pytest_plugins = ["pytester"]

IS_PYTEST_BENCHMARK_INSTALLED = pkgutil.find_loader("pytest_benchmark") is not None
skip_without_pytest_benchmark = pytest.mark.skipif(
    not IS_PYTEST_BENCHMARK_INSTALLED, reason="pytest_benchmark not installed"
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
    not IS_VALGRIND_INSTALLED, reason="valgrind not installed"
)

if IS_VALGRIND_INSTALLED:
    print("NOTICE: Testing with valgrind compatibility", file=sys.stderr, flush=True)
