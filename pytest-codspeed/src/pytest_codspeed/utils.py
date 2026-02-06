from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from codspeed.utils import get_environment_metadata as _get_environment_metadata
from codspeed.utils import get_git_relative_path
from pytest_codspeed import __semver_version__

IS_PYTEST_BENCHMARK_INSTALLED = importlib.util.find_spec("pytest_benchmark") is not None
IS_PYTEST_SPEED_INSTALLED = importlib.util.find_spec("pytest_speed") is not None
BEFORE_PYTEST_8_1_1 = pytest.version_tuple < (8, 1, 1)


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
    return _get_environment_metadata("pytest-codspeed", __semver_version__)
