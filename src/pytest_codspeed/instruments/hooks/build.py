from pathlib import Path

from cffi import FFI  # type: ignore

ffibuilder = FFI()

includes_dir = Path(__file__).parent.joinpath("instrument-hooks/includes")
header_text = (includes_dir / "core.h").read_text()


# Manually copied from `instrument-hooks/includes/core.h` to avoid parsing issues
ffibuilder.cdef("""
typedef uint64_t *InstrumentHooks;

InstrumentHooks *instrument_hooks_init(void);
void instrument_hooks_deinit(InstrumentHooks *);

bool instrument_hooks_is_instrumented(InstrumentHooks *);
uint8_t instrument_hooks_start_benchmark(InstrumentHooks *);
uint8_t instrument_hooks_stop_benchmark(InstrumentHooks *);
uint8_t instrument_hooks_set_executed_benchmark(InstrumentHooks *, int32_t pid,
                                               const char *uri);
uint8_t instrument_hooks_set_integration(InstrumentHooks *, const char *name,
                                        const char *version);

#define MARKER_TYPE_SAMPLE_START 0
#define MARKER_TYPE_SAMPLE_END 1
#define MARKER_TYPE_BENCHMARK_START 2
#define MARKER_TYPE_BENCHMARK_END 3

uint8_t instrument_hooks_add_marker(InstrumentHooks *, uint32_t pid,
                                   uint8_t marker_type, uint64_t timestamp);
uint64_t instrument_hooks_current_timestamp(void);

void callgrind_start_instrumentation();
void callgrind_stop_instrumentation();

void instrument_hooks_set_feature(uint64_t feature, bool enabled);
""")

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
