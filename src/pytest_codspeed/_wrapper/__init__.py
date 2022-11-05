from cffi import FFI
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .wrapper import lib as _lib


def _get_ffi():
    ffi = FFI()
    with open("src/pytest_codspeed/_wrapper/wrapper.h") as f:
        ffi.cdef(f.read())
    ffi.set_source(
        "dist_callgrind_wrapper",
        '#include "wrapper.h"',
        sources=["wrapper.c"],
    )
    return ffi


def get_lib() -> "_lib":
    try:
        ffi = _get_ffi()
        ffi.compile(
            target="dist_callgrind_wrapper.*",
            tmpdir="src/pytest_codspeed/_wrapper",
        )
        from .dist_callgrind_wrapper import lib

        return lib
    except Exception as e:
        raise Exception("Failed to compile the wrapper") from e
