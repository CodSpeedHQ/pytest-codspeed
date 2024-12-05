from pathlib import Path

from cffi import FFI  # type: ignore

wrapper_dir = Path(__file__).parent

ffibuilder = FFI()

ffibuilder.cdef((wrapper_dir / "wrapper.h").read_text())

ffibuilder.set_source(
    "pytest_codspeed.instruments.valgrind._wrapper.dist_callgrind_wrapper",
    '#include "wrapper.h"',
    sources=["src/pytest_codspeed/instruments/valgrind/_wrapper/wrapper.c"],
    include_dirs=[str(wrapper_dir)],
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
