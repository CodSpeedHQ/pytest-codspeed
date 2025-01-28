import json

import pytest
from conftest import run_pytest_codspeed_with_mode
from inline_snapshot import snapshot

from pytest_codspeed.instruments import MeasurementMode
from pytest_codspeed.instruments.valgrind import ValgrindInstrument
from pytest_codspeed.instruments.walltime import WallTimeInstrument


@pytest.mark.parametrize(
    "mode", [MeasurementMode.WallTime, MeasurementMode.Instrumentation]
)
def test_benchmark_results(pytester: pytest.Pytester, mode: MeasurementMode) -> None:
    pytester.makepyfile(
        """
        import time, pytest

        def test_no_parametrization(benchmark):
            benchmark(lambda: 1 + 1)

        class TestClass:
            class TestNested:
                @pytest.mark.benchmark(group="bench-group")
                @pytest.mark.parametrize("a,b", [("foo","bar"), (12,13), (58.3,"baz")])
                def test_fully_parametrized(self, benchmark, a, b):
                    benchmark(lambda: 1 + 1)
        """
    )
    result = run_pytest_codspeed_with_mode(pytester, mode)
    result.stdout.fnmatch_lines_random(["*4 benchmark*"])

    with open(next(pytester.path.joinpath(".codspeed").glob("*.json"))) as file:
        results = json.loads(file.read())
        assert (
            results.get("instrument").get("type") == ValgrindInstrument.instrument
            if mode == MeasurementMode.Instrumentation
            else WallTimeInstrument.instrument
        )

        benchmarks = results.get("benchmarks")
        if mode == MeasurementMode.WallTime:
            for b in benchmarks:
                del b["stats"]
                del b["config"]
        assert benchmarks == snapshot(
            [
                {
                    "file": "test_benchmark_results.py",
                    "module": "",
                    "groups": [],
                    "name": "test_no_parametrization",
                    "args": [],
                    "args_names": [],
                },
                {
                    "file": "test_benchmark_results.py",
                    "module": "TestClass::TestNested",
                    "groups": ["bench-group"],
                    "name": "test_fully_parametrized",
                    "args": ["foo", "bar"],
                    "args_names": ["a", "b"],
                },
                {
                    "file": "test_benchmark_results.py",
                    "module": "TestClass::TestNested",
                    "groups": ["bench-group"],
                    "name": "test_fully_parametrized",
                    "args": [12, 13],
                    "args_names": ["a", "b"],
                },
                {
                    "file": "test_benchmark_results.py",
                    "module": "TestClass::TestNested",
                    "groups": ["bench-group"],
                    "name": "test_fully_parametrized",
                    "args": [58.3, "baz"],
                    "args_names": ["a", "b"],
                },
            ]
        )
