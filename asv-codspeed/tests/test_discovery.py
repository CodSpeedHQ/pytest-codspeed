"""Tests for ASV benchmark discovery."""

from __future__ import annotations

from asv_codspeed.discovery import discover_benchmarks


def test_discover_simple_functions(tmp_benchmarks):
    """Test discovery of module-level time_* functions."""
    bench_dir = tmp_benchmarks(
        {
            "bench_basic.py": """
def time_addition():
    return 1 + 1

def time_multiplication():
    return 2 * 3

def not_a_benchmark():
    pass
"""
        }
    )
    benchmarks = discover_benchmarks(bench_dir)
    names = [b.name for b in benchmarks]
    assert "bench_basic.time_addition" in names
    assert "bench_basic.time_multiplication" in names
    assert all("not_a_benchmark" not in n for n in names)
    assert all(b.type == "time" for b in benchmarks)


def test_discover_class_methods(tmp_benchmarks):
    """Test discovery of time_* methods inside classes."""
    bench_dir = tmp_benchmarks(
        {
            "bench_class.py": """
class TimeSuite:
    def time_method_one(self):
        pass

    def time_method_two(self):
        pass

    def helper(self):
        pass
"""
        }
    )
    benchmarks = discover_benchmarks(bench_dir)
    names = [b.name for b in benchmarks]
    assert len(benchmarks) == 2
    assert any("time_method_one" in n for n in names)
    assert any("time_method_two" in n for n in names)
    assert all("helper" not in n for n in names)


def test_discover_class_with_setup_teardown(tmp_benchmarks):
    """Test that setup and teardown are properly attached."""
    bench_dir = tmp_benchmarks(
        {
            "bench_lifecycle.py": """
class TimeSuite:
    def setup(self):
        self.data = [1, 2, 3]

    def teardown(self):
        del self.data

    def time_process(self):
        sum(self.data)
"""
        }
    )
    benchmarks = discover_benchmarks(bench_dir)
    assert len(benchmarks) == 1
    bench = benchmarks[0]
    assert bench.setup is not None
    assert bench.teardown is not None


def test_discover_parameterized(tmp_benchmarks):
    """Test discovery of parameterized benchmarks."""
    bench_dir = tmp_benchmarks(
        {
            "bench_params.py": """
class TimeParams:
    params = [10, 100, 1000]
    param_names = ["n"]

    def time_range(self, n):
        for i in range(n):
            pass
"""
        }
    )
    benchmarks = discover_benchmarks(bench_dir)
    assert len(benchmarks) == 3
    names = [b.name for b in benchmarks]
    assert any("10" in n for n in names)
    assert any("100" in n and "1000" not in n for n in names)
    assert any("1000" in n for n in names)
    # Verify params are set correctly
    for bench in benchmarks:
        assert bench.current_param_values is not None
        assert len(bench.current_param_values) == 1


def test_discover_multi_param(tmp_benchmarks):
    """Test discovery of multi-parameter benchmarks."""
    bench_dir = tmp_benchmarks(
        {
            "bench_multi.py": """
class TimeMultiParam:
    params = [[10, 100], ["a", "b"]]
    param_names = ["n", "label"]

    def time_combo(self, n, label):
        pass
"""
        }
    )
    benchmarks = discover_benchmarks(bench_dir)
    # 2 x 2 = 4 combinations
    assert len(benchmarks) == 4


def test_discover_empty_directory(tmp_path):
    """Test discovery in an empty directory."""
    bench_dir = tmp_path / "benchmarks"
    bench_dir.mkdir()
    benchmarks = discover_benchmarks(bench_dir)
    assert benchmarks == []


def test_discover_nonexistent_directory(tmp_path):
    """Test discovery in a nonexistent directory."""
    benchmarks = discover_benchmarks(tmp_path / "nonexistent")
    assert benchmarks == []


def test_discover_skips_underscore_files(tmp_benchmarks):
    """Test that files starting with _ are skipped."""
    bench_dir = tmp_benchmarks(
        {
            "_helper.py": """
def time_should_not_be_found():
    pass
""",
            "bench_real.py": """
def time_real():
    pass
""",
        }
    )
    benchmarks = discover_benchmarks(bench_dir)
    names = [b.name for b in benchmarks]
    assert len(benchmarks) == 1
    assert "bench_real.time_real" in names


def test_discover_filter_pattern(tmp_benchmarks):
    """Test filtering benchmarks by regex pattern."""
    bench_dir = tmp_benchmarks(
        {
            "bench_filter.py": """
def time_foo():
    pass

def time_bar():
    pass

def time_baz():
    pass
"""
        }
    )
    benchmarks = discover_benchmarks(bench_dir, filter_pattern="foo|bar")
    names = [b.name for b in benchmarks]
    assert len(benchmarks) == 2
    assert any("foo" in n for n in names)
    assert any("bar" in n for n in names)
    assert all("baz" not in n for n in names)


def test_discover_different_benchmark_types(tmp_benchmarks):
    """Test that different benchmark types are identified correctly."""
    bench_dir = tmp_benchmarks(
        {
            "bench_types.py": """
def time_something():
    pass

def track_value():
    return 42

def mem_object():
    return [0] * 1000

def peakmem_process():
    pass
"""
        }
    )
    benchmarks = discover_benchmarks(bench_dir)
    types = {b.name: b.type for b in benchmarks}
    assert types["bench_types.time_something"] == "time"
    assert types["bench_types.track_value"] == "track"
    assert types["bench_types.mem_object"] == "mem"
    assert types["bench_types.peakmem_process"] == "peakmem"


def test_discover_sample_benchmarks(sample_benchmarks_dir):
    """Test discovery of the sample benchmark files."""
    benchmarks = discover_benchmarks(sample_benchmarks_dir)
    time_benchmarks = [b for b in benchmarks if b.type == "time"]
    assert len(time_benchmarks) >= 4  # At least the 4 non-parameterized ones
