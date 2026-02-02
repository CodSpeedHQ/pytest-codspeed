"""Tests for the asv-codspeed CLI."""

from __future__ import annotations

import json
import subprocess
import sys


def test_cli_version():
    """Test that --version works."""
    result = subprocess.run(
        [sys.executable, "-m", "asv_codspeed", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "asv-codspeed" in result.stdout


def test_cli_run_help():
    """Test that 'run --help' works."""
    result = subprocess.run(
        [sys.executable, "-m", "asv_codspeed", "run", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "benchmark_dir" in result.stdout
    assert "--mode" in result.stdout


def test_cli_run_benchmarks(tmp_path):
    """Test running benchmarks via CLI."""
    bench_dir = tmp_path / "benchmarks"
    bench_dir.mkdir()
    (bench_dir / "bench_test.py").write_text(
        """
def time_hello():
    return "hello"
"""
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "asv_codspeed",
            "run",
            str(bench_dir),
            "--mode",
            "walltime",
            "--warmup-time",
            "0",
            "--max-rounds",
            "2",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "time_hello" in result.stdout
    assert "Results saved to" in result.stdout


def test_cli_run_with_filter(tmp_path):
    """Test running with --bench filter."""
    bench_dir = tmp_path / "benchmarks"
    bench_dir.mkdir()
    (bench_dir / "bench_test.py").write_text(
        """
def time_foo():
    pass

def time_bar():
    pass
"""
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "asv_codspeed",
            "run",
            str(bench_dir),
            "--mode",
            "walltime",
            "--warmup-time",
            "0",
            "--max-rounds",
            "2",
            "--bench",
            "foo",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "time_foo" in result.stdout

    # Verify only filtered benchmark ran
    result_files = list(bench_dir.glob(".codspeed/results_*.json"))
    assert len(result_files) == 1
    data = json.loads(result_files[0].read_text())
    assert len(data["benchmarks"]) == 1
    assert "foo" in data["benchmarks"][0]["name"]


def test_cli_run_empty_dir(tmp_path):
    """Test running with no benchmarks found returns non-zero."""
    bench_dir = tmp_path / "empty"
    bench_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "asv_codspeed",
            "run",
            str(bench_dir),
            "--mode",
            "walltime",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_cli_no_command():
    """Test that running without a command shows an error."""
    result = subprocess.run(
        [sys.executable, "-m", "asv_codspeed"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2  # argparse exits with 2 for missing args
