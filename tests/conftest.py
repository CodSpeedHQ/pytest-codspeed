import pkgutil
import shutil
import sys

import pytest

pytest_plugins = ["pytester"]

if pkgutil.find_loader("pytest_benchmark") is not None:
    pytest_plugins.append("pytest_benchmark")
    print(
        "NOTICE: Testing with pytest-benchmark compatibility",
        file=sys.stderr,
        flush=True,
    )

VALGRIND_INSTALLED = shutil.which("valgrind") is not None
skip_without_valgrind = pytest.mark.skipif(
    not VALGRIND_INSTALLED, reason="valgrind not installed"
)

if VALGRIND_INSTALLED:
    print("NOTICE: Testing with valgrind compatibility", file=sys.stderr, flush=True)
