"""Tests for the ASV benchmark runner."""

from __future__ import annotations

import json

from asv_codspeed.runner import run_benchmarks

from codspeed.instruments import MeasurementMode


def test_run_simple_benchmarks_walltime(tmp_benchmarks):
    """Test running simple benchmarks in walltime mode."""
    bench_dir = tmp_benchmarks(
        {
            "bench_simple.py": """
def time_addition():
    return 1 + 1

def time_loop():
    for i in range(100):
        pass
"""
        }
    )
    result = run_benchmarks(
        benchmark_dir=bench_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
    )
    assert result == 0

    # Verify results file was created
    result_files = list(bench_dir.glob(".codspeed/results_*.json"))
    assert len(result_files) == 1

    data = json.loads(result_files[0].read_text())
    assert data["creator"]["name"] == "pytest-codspeed"
    assert data["instrument"]["type"] == "walltime"
    assert len(data["benchmarks"]) == 2


def test_run_with_setup_teardown(tmp_benchmarks):
    """Test running benchmarks with setup and teardown."""
    bench_dir = tmp_benchmarks(
        {
            "bench_lifecycle.py": """
class TimeSuite:
    def setup(self):
        self.data = list(range(100))

    def teardown(self):
        pass

    def time_sort(self):
        sorted(self.data)
"""
        }
    )
    result = run_benchmarks(
        benchmark_dir=bench_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
    )
    assert result == 0


def test_run_parameterized_benchmarks(tmp_benchmarks):
    """Test running parameterized benchmarks."""
    bench_dir = tmp_benchmarks(
        {
            "bench_params.py": """
class TimeRange:
    params = [10, 100]
    param_names = ["n"]

    def time_loop(self, n):
        for i in range(n):
            pass
"""
        }
    )
    result = run_benchmarks(
        benchmark_dir=bench_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
    )
    assert result == 0

    result_files = list(bench_dir.glob(".codspeed/results_*.json"))
    assert len(result_files) == 1

    data = json.loads(result_files[0].read_text())
    assert len(data["benchmarks"]) == 2  # 2 parameter values


def test_run_no_benchmarks_found(tmp_path):
    """Test running when no benchmarks are found."""
    bench_dir = tmp_path / "empty_benchmarks"
    bench_dir.mkdir()
    (bench_dir / "no_bench.py").write_text("def helper(): pass\n")

    result = run_benchmarks(
        benchmark_dir=bench_dir,
        mode=MeasurementMode.WallTime,
    )
    assert result == 1


def test_run_nonexistent_dir(tmp_path):
    """Test running with a nonexistent benchmark directory."""
    result = run_benchmarks(
        benchmark_dir=tmp_path / "nonexistent",
        mode=MeasurementMode.WallTime,
    )
    assert result == 1


def test_run_with_filter(tmp_benchmarks):
    """Test running with a benchmark filter."""
    bench_dir = tmp_benchmarks(
        {
            "bench_filter.py": """
def time_included():
    return 1 + 1

def time_excluded():
    return 2 + 2
"""
        }
    )
    result = run_benchmarks(
        benchmark_dir=bench_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
        bench_filter="included",
    )
    assert result == 0

    result_files = list(bench_dir.glob(".codspeed/results_*.json"))
    data = json.loads(result_files[0].read_text())
    assert len(data["benchmarks"]) == 1
    assert "included" in data["benchmarks"][0]["name"]


def test_result_json_format(tmp_benchmarks):
    """Test that the result JSON has the expected structure."""
    bench_dir = tmp_benchmarks(
        {
            "bench_format.py": """
def time_test():
    return sum(range(100))
"""
        }
    )
    run_benchmarks(
        benchmark_dir=bench_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
    )

    result_files = list(bench_dir.glob(".codspeed/results_*.json"))
    data = json.loads(result_files[0].read_text())

    # Verify top-level structure
    assert "creator" in data
    assert "python" in data
    assert "instrument" in data
    assert "benchmarks" in data

    # Verify creator
    assert data["creator"]["name"] == "pytest-codspeed"
    assert "version" in data["creator"]
    assert "pid" in data["creator"]

    # Verify python metadata
    assert "sysconfig" in data["python"]
    assert "dependencies" in data["python"]

    # Verify instrument
    assert data["instrument"]["type"] == "walltime"
    assert "clock_info" in data["instrument"]

    # Verify benchmark entry
    bench = data["benchmarks"][0]
    assert "name" in bench
    assert "uri" in bench
    assert "config" in bench
    assert "stats" in bench

    stats = bench["stats"]
    assert "min_ns" in stats
    assert "max_ns" in stats
    assert "mean_ns" in stats
    assert "stdev_ns" in stats
    assert "rounds" in stats


def test_run_sample_benchmarks(sample_benchmarks_dir):
    """Test running the sample benchmarks."""
    result = run_benchmarks(
        benchmark_dir=sample_benchmarks_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
    )
    assert result == 0

    # Clean up
    import shutil

    codspeed_dir = sample_benchmarks_dir / ".codspeed"
    if codspeed_dir.exists():
        shutil.rmtree(codspeed_dir)


def test_run_to_profile_folder(tmp_benchmarks, tmp_path):
    """Test running with a custom profile folder."""
    bench_dir = tmp_benchmarks(
        {
            "bench_profile.py": """
def time_test():
    return 1 + 1
"""
        }
    )
    profile_folder = tmp_path / "profiles"

    result = run_benchmarks(
        benchmark_dir=bench_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
        profile_folder=profile_folder,
    )
    assert result == 0

    result_files = list(profile_folder.glob("results/*.json"))
    assert len(result_files) == 1


def test_run_recursive_fibo_10(tmp_benchmarks):
    """Test running a recursive Fibonacci(10) benchmark."""
    bench_dir = tmp_benchmarks(
        {
            "bench_fibo.py": """
def _fibo(n):
    if n <= 1:
        return n
    return _fibo(n - 1) + _fibo(n - 2)

def time_recursive_fibo_10():
    _fibo(10)
"""
        }
    )
    result = run_benchmarks(
        benchmark_dir=bench_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
    )
    assert result == 0

    result_files = list(bench_dir.glob(".codspeed/results_*.json"))
    assert len(result_files) == 1

    data = json.loads(result_files[0].read_text())
    assert len(data["benchmarks"]) == 1
    assert data["benchmarks"][0]["name"] == "bench_fibo.time_recursive_fibo_10"
    assert data["benchmarks"][0]["stats"]["mean_ns"] > 0


def test_run_foo_bar_baz(tmp_benchmarks):
    """Test running foo, bar, and baz benchmarks."""
    bench_dir = tmp_benchmarks(
        {
            "bench_foo_bar_baz.py": """
def time_foo():
    total = 0
    for i in range(500):
        total += i
    return total

def time_bar():
    data = list(range(200))
    return sorted(data, reverse=True)

def time_baz():
    return {k: k * k for k in range(300)}
"""
        }
    )
    result = run_benchmarks(
        benchmark_dir=bench_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
    )
    assert result == 0

    result_files = list(bench_dir.glob(".codspeed/results_*.json"))
    data = json.loads(result_files[0].read_text())
    assert len(data["benchmarks"]) == 3

    names = {b["name"] for b in data["benchmarks"]}
    assert "bench_foo_bar_baz.time_foo" in names
    assert "bench_foo_bar_baz.time_bar" in names
    assert "bench_foo_bar_baz.time_baz" in names

    # All should report as pytest-codspeed
    assert data["creator"]["name"] == "pytest-codspeed"


def test_run_recursive_fibo_10_sample(sample_benchmarks_dir):
    """Test running the fibo sample benchmark from sample_benchmarks."""
    result = run_benchmarks(
        benchmark_dir=sample_benchmarks_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
        bench_filter="fibo",
    )
    assert result == 0

    import shutil

    codspeed_dir = sample_benchmarks_dir / ".codspeed"
    if codspeed_dir.exists():
        shutil.rmtree(codspeed_dir)


def test_run_foo_bar_baz_sample(sample_benchmarks_dir):
    """Test running the foo/bar/baz sample benchmarks from sample_benchmarks."""
    result = run_benchmarks(
        benchmark_dir=sample_benchmarks_dir,
        mode=MeasurementMode.WallTime,
        warmup_time=0,
        max_rounds=2,
        bench_filter="foo_bar_baz",
    )
    assert result == 0

    import shutil

    codspeed_dir = sample_benchmarks_dir / ".codspeed"
    if codspeed_dir.exists():
        shutil.rmtree(codspeed_dir)
