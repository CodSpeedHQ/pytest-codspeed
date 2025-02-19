import importlib
import sys
import time
import pytest
from unittest import mock

@pytest.mark.parametrize("mod_name", [".module_a", ".module_b"])
def test_bench_module_import(benchmark, mod_name):
    @benchmark
    def _():
        with mock.patch("sys.modules", {}):
            importlib.import_module(mod_name, "test_bench_imports")


