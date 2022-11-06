import os
from typing import TYPE_CHECKING

from cffi import FFI  # type: ignore

if TYPE_CHECKING:
    from .wrapper import lib as LibType

_wrapper_dir = os.path.dirname(os.path.abspath(__file__))


def _get_ffi():
    ffi = FFI()
    with open(f"{_wrapper_dir}/wrapper.h") as f:
        ffi.cdef(f.read())
    ffi.set_source(
        "dist_callgrind_wrapper",
        '#include "wrapper.h"',
        sources=["wrapper.c"],
    )
    return ffi


def get_lib() -> "LibType":
    try:
        ffi = _get_ffi()
        ffi.compile(
            target="dist_callgrind_wrapper.*",
            tmpdir=_wrapper_dir,
        )
        from .dist_callgrind_wrapper import lib  # type: ignore

        return lib
    except Exception as e:
        raise Exception("Failed to compile the wrapper") from e
