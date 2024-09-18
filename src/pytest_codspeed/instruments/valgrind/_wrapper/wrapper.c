#include <valgrind/callgrind.h>

void start_instrumentation() {
    CALLGRIND_START_INSTRUMENTATION;
}

void stop_instrumentation() {
    CALLGRIND_STOP_INSTRUMENTATION;
}

void dump_stats() {
    CALLGRIND_DUMP_STATS;
}

void dump_stats_at(char *s) {
    CALLGRIND_DUMP_STATS_AT(s);
}

void zero_stats() {
    CALLGRIND_ZERO_STATS;
}

void toggle_collect() {
    CALLGRIND_TOGGLE_COLLECT;
}
