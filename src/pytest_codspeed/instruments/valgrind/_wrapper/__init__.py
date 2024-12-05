from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .wrapper import lib as LibType


def get_lib() -> LibType:
    try:
        from .dist_callgrind_wrapper import lib  # type: ignore

        return lib
    except Exception as e:
        raise Exception("Failed to get a compiled wrapper") from e
