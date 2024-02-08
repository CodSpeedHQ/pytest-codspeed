from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest import CaptureFixture


@pytest.mark.benchmark
def test_print():
    """Test print statements are captured by pytest (i.e., not printed to terminal in
    the middle of the progress bar) and only displayed after test run (on failures)."""
    print("print to stdout")
    print("print to stderr", file=sys.stderr)


@pytest.mark.benchmark
def test_capsys(capsys: CaptureFixture):
    """Test print statements are captured by capsys (i.e., not printed to terminal in
    the middle of the progress bar) and can be inspected within test."""
    print("print to stdout")
    print("print to stderr", file=sys.stderr)

    stdout, stderr = capsys.readouterr()

    assert stdout == "print to stdout\n"
    assert stderr == "print to stderr\n"
