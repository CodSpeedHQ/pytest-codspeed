import os
from typing import TYPE_CHECKING

from cffi import FFI  # type: ignore
from filelock import FileLock

from .. import __version__

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
        build_lock = FileLock(f"{_wrapper_dir}/build.lock")
        with build_lock:
            is_target_already_built = any(
                target.startswith(f"dist_callgrind_wrapper.{__version__}.")
                for target in os.listdir(_wrapper_dir)
            )
            if not is_target_already_built:
                ffi = _get_ffi()
                ffi.compile(
                    target=f"dist_callgrind_wrapper.{__version__}.*",
                    tmpdir=_wrapper_dir,
                )

        from .dist_callgrind_wrapper import lib  # type: ignore

        return lib
    except Exception as e:
        raise Exception("Failed to compile the wrapper") from e
