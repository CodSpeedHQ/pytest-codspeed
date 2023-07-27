from pathlib import Path


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


def get_git_relative_uri(uri: str, pytest_rootdir: Path) -> str:
    """Get the benchmark uri relative to the git root dir.

    Args:
        uri (str): the benchmark uri, for example:
          testing/test_excinfo.py::TestFormattedExcinfo::test_repr_source
        pytest_rootdir (str): the pytest root dir, for example:
          /home/user/gitrepo/folder

    Returns:
        str: the benchmark uri relative to the git root dir, for example:
          folder/testing/test_excinfo.py::TestFormattedExcinfo::test_repr_source

    """
    file_path, function_path = uri.split("::", 1)
    absolute_file_path = pytest_rootdir / Path(file_path)
    relative_git_path = get_git_relative_path(absolute_file_path)
    return f"{str(relative_git_path)}::{function_path}"
