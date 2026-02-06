from __future__ import annotations

from pathlib import Path

import pytest

SAMPLE_BENCHMARKS_DIR = Path(__file__).parent / "sample_benchmarks"


@pytest.fixture
def sample_benchmarks_dir():
    return SAMPLE_BENCHMARKS_DIR


@pytest.fixture
def tmp_benchmarks(tmp_path):
    """Create a temporary directory with benchmark files."""

    def _create(files: dict[str, str]) -> Path:
        bench_dir = tmp_path / "benchmarks"
        bench_dir.mkdir()
        for name, content in files.items():
            (bench_dir / name).write_text(content)
        return bench_dir

    return _create
