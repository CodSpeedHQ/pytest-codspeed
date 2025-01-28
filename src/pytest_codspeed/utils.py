from __future__ import annotations

import os
import sys
import sysconfig
from pathlib import Path

from pytest_codspeed import __semver_version__

if sys.version_info < (3, 10):
    import importlib_metadata as importlib_metadata
else:
    import importlib.metadata as importlib_metadata


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
