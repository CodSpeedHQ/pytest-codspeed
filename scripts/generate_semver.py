"""
This script converts a PyPI version string to a semantic version string and updates the
__semver_version__ variable in the __init__.py file of the pytest_codspeed package.
"""

import re
from pathlib import Path

from packaging.version import Version as PyPIVersion
from semver import Version as SemVerVersion


def pypi_version_to_semver(pypi_version_str: str) -> str:
    py_version = PyPIVersion(pypi_version_str)
    if py_version.epoch != 0:
        raise ValueError("Can't convert an epoch to semver")
    if py_version.post is not None:
        raise ValueError("Can't convert a post part to semver")

    pre = None if not py_version.pre else "".join([str(i) for i in py_version.pre])
    semver = SemVerVersion(*py_version.release, prerelease=pre, build=py_version.dev)
    return str(semver)


def main():
    from pytest_codspeed import __version__ as pypi_version

    semver_version = pypi_version_to_semver(pypi_version)
    init_file_path = Path("./src/pytest_codspeed/__init__.py")
    content = init_file_path.read_text()

    content = re.sub(
        r'__semver_version__\s*=\s*".*"',
        f'__semver_version__ = "{semver_version}"',
        content,
    )
    init_file_path.write_text(content)


if __name__ == "__main__":
    main()
