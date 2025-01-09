import tempfile
from contextlib import contextmanager
from pathlib import Path

from pytest_codspeed.utils import get_git_relative_path


@contextmanager
def TemporaryGitRepo():
    with tempfile.TemporaryDirectory() as tmpdirname:
        (Path(tmpdirname) / ".git").mkdir(parents=True)
        yield tmpdirname


def test_get_git_relative_path_found():
    with TemporaryGitRepo() as tmp_repo:
        path = Path(tmp_repo) / "folder/nested_folder"
        assert get_git_relative_path(path) == Path("folder/nested_folder")


def test_get_git_relative_path_not_found():
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "folder"
        assert get_git_relative_path(path) == path
