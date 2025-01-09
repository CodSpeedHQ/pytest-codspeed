import pytest

from pytest_codspeed.plugin import Benchmark


class ClassWithStr:
    def __str__(self):
        return "class_str"


benchmarks = [
    Benchmark(
        file="test_benchmark_results.py",
        module="TestClass::TestNested",
        groups=["bench-group"],
        name="test_fully_parametrized",
        args=[58.3, "baz"],
        args_names=["a", "b"],
    ),
    Benchmark(
        file="another_test_file.py",
        module="AnotherClass::AnotherTest",
        groups=["another-group"],
        name="test_another_case",
        args=[42, "foo"],
        args_names=["x", "y"],
    ),
    Benchmark(
        file="yet_another_test_file.py",
        module="",
        groups=[],
        name="test_yet_another_case",
        args=[],
        args_names=[],
    ),
    Benchmark(
        file="test_complex_args.py",
        module="",
        groups=[],
        name="test_complex_args",
        args=[{"a": 1, "b": 2}, "foo", None, [{"a": 1, "b": 2}, "foo"], ClassWithStr()],
        args_names=["x", "y", "z", "w", "u"],
    ),
]


@pytest.mark.parametrize(
    "bench, expected_json",
    [
        (
            benchmarks[0],
            '{"args":[58.3,"baz"],"args_names":["a","b"],"file":"test_benchmark_results.py","groups":["bench-group"],"module":"TestClass::TestNested","name":"test_fully_parametrized"}',
        ),
        (
            benchmarks[1],
            '{"args":[42,"foo"],"args_names":["x","y"],"file":"another_test_file.py","groups":["another-group"],"module":"AnotherClass::AnotherTest","name":"test_another_case"}',
        ),
        (
            benchmarks[2],
            '{"args":[],"args_names":[],"file":"yet_another_test_file.py","groups":[],"module":"","name":"test_yet_another_case"}',
        ),
        (
            benchmarks[3],
            '{"args":[{"a":1,"b":2},"foo",null,[{"a":1,"b":2},"foo"],{}],"args_names":["x","y","z","w","u"],"file":"test_complex_args.py","groups":[],"module":"","name":"test_complex_args"}',
        ),
    ],
)
def test_benchmark_to_json(bench, expected_json):
    assert bench.to_json_string() == expected_json


@pytest.mark.parametrize(
    "bench, expected_display_name",
    [
        (benchmarks[0], "test_fully_parametrized[58.3-baz]"),
        (benchmarks[1], "test_another_case[42-foo]"),
        (benchmarks[2], "test_yet_another_case"),
        (benchmarks[3], "test_complex_args[x0-foo-z2-w3-class_str]"),
    ],
)
def test_benchmark_display_name(bench, expected_display_name):
    assert bench.display_name == expected_display_name
