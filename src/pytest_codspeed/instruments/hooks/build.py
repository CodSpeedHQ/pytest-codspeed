from pathlib import Path

from cffi import FFI  # type: ignore

ffibuilder = FFI()

includes_dir = Path(__file__).parent.joinpath("instrument-hooks/includes")
header_text = (includes_dir / "core.h").read_text()
filtered_header = "\n".join(
    line for line in header_text.splitlines() if not line.strip().startswith("#")
)
ffibuilder.cdef(filtered_header)

ffibuilder.set_source(
    "pytest_codspeed.instruments.hooks.dist_instrument_hooks",
    """
    #include "core.h"
    """,
    sources=[
        "src/pytest_codspeed/instruments/hooks/instrument-hooks/dist/core.c",
    ],
    include_dirs=[str(includes_dir)],
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
