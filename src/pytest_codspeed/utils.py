from __future__ import annotations

import importlib.util
import os
import sys
import sysconfig
from pathlib import Path

import pytest

from pytest_codspeed import __semver_version__

if sys.version_info < (3, 10):
    import importlib_metadata as importlib_metadata
else:
    import importlib.metadata as importlib_metadata


IS_PYTEST_BENCHMARK_INSTALLED = importlib.util.find_spec("pytest_benchmark") is not None
IS_PYTEST_SPEED_INSTALLED = importlib.util.find_spec("pytest_speed") is not None
BEFORE_PYTEST_8_1_1 = pytest.version_tuple < (8, 1, 1)
SUPPORTS_PERF_TRAMPOLINE = sysconfig.get_config_var("PY_HAVE_PERF_TRAMPOLINE") == 1


def get_git_relative_path(abs_path: Path) -> Path:
    """Get the path relative to the git root directory. If the path is not
    inside a git repository, the original path itself is returned.
    """
    git_path = Path(abs_path).resolve()
    while (
        git_path != git_path.parent
    ):  # stops at root since parent of root is root itself
        if (git_path / ".git").exists():
            return abs_path.resolve().relative_to(git_path)
        git_path = git_path.parent
    return abs_path


def get_git_relative_uri_and_name(nodeid: str, pytest_rootdir: Path) -> tuple[str, str]:
    """Get the benchmark uri relative to the git root dir and the benchmark name.

    Args:
        nodeid (str): the pytest nodeid, for example:
          testing/test_excinfo.py::TestFormattedExcinfo::test_repr_source
        pytest_rootdir (str): the pytest root dir, for example:
          /home/user/gitrepo/folder

    Returns:
        str: the benchmark uri relative to the git root dir, for example:
          folder/testing/test_excinfo.py::TestFormattedExcinfo::test_repr_source

    """
    file_path, bench_name = nodeid.split("::", 1)
    absolute_file_path = pytest_rootdir / Path(file_path)
    relative_git_path = get_git_relative_path(absolute_file_path)
    return (f"{str(relative_git_path)}::{bench_name}", bench_name)


def get_environment_metadata() -> dict[str, dict]:
    return {
        "creator": {
            "name": "pytest-codspeed",
            "version": __semver_version__,
            "pid": os.getpid(),
        },
        "python": {
            "sysconfig": sysconfig.get_config_vars(),
            "dependencies": {
                d.name: d.version for d in importlib_metadata.distributions()
            },
        },
    }
