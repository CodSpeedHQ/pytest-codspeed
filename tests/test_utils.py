from pathlib import Path
from unittest.mock import patch

from pytest_codspeed.utils import get_git_relative_path, get_git_relative_uri


def test_get_git_relative_path_found():
    with patch.object(
        Path, "exists", lambda self: str(self) == "/home/user/gitrepo/.git"
    ):
        path = Path("/home/user/gitrepo/folder/nested_folder")
        assert get_git_relative_path(path) == Path("folder/nested_folder")


def test_get_git_relative_path_not_found():
    with patch.object(Path, "exists", lambda self: False):
        path = Path("/home/user/gitrepo/folder")
        assert get_git_relative_path(path) == path


def test_get_git_relative_uri():
    with patch.object(
        Path, "exists", lambda self: str(self) == "/home/user/gitrepo/.git"
    ):
        pytest_rootdir = Path("/home/user/gitrepo/pytest_root")
        uri = "testing/test_excinfo.py::TestFormattedExcinfo::test_fn"
        assert (
            get_git_relative_uri(uri, pytest_rootdir)
            == "pytest_root/testing/test_excinfo.py::TestFormattedExcinfo::test_fn"
        )
