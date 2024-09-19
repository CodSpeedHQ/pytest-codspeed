import pytest
from generate_semver import pypi_version_to_semver


def test_pypi_version_to_semver_valid():
    # Test cases for valid PyPI version strings
    assert pypi_version_to_semver("1.0.0") == "1.0.0"
    assert pypi_version_to_semver("1.0.0a1") == "1.0.0-a1"
    assert pypi_version_to_semver("1.0.0b1") == "1.0.0-b1"
    assert pypi_version_to_semver("1.0.0rc1") == "1.0.0-rc1"


def test_pypi_version_to_semver_invalid():
    # Test cases for invalid PyPI version strings that should raise ValueError
    with pytest.raises(ValueError, match="Can't convert an epoch to semver"):
        pypi_version_to_semver("1!1.0.0")

    with pytest.raises(ValueError, match="Can't convert a post part to semver"):
        pypi_version_to_semver("1.0.0.post")
