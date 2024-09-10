from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from pytest_codspeed import __version__
from pytest_codspeed._wrapper import get_lib
from pytest_codspeed.instruments import Instrument

if TYPE_CHECKING:
    from typing import Callable

    from pytest import Session

    from pytest_codspeed.instruments import P, T

SUPPORTS_PERF_TRAMPOLINE = sys.version_info >= (3, 12)


class InstrumentationInstrument(Instrument):
    def __init__(self):
        self.benchmark_count = 0
        self.should_measure = os.environ.get("CODSPEED_ENV") is not None
        if self.should_measure:
            self.lib = get_lib()
            self.lib.dump_stats_at(
                f"Metadata: pytest-codspeed {__version__}".encode("ascii")
            )
            if SUPPORTS_PERF_TRAMPOLINE:
                sys.activate_stack_trampoline("perf")
        else:
            self.lib = None

    def get_instrument_config_str_and_warns(self) -> tuple[str, list[str]]:
        config = (
            f"mode: instrumentation, "
            f"callgraph: {'enabled' if SUPPORTS_PERF_TRAMPOLINE  else 'not supported'}"
        )
        warnings = []
        if not self.should_measure:
            warnings.append(
                "\033[1m"
                "NOTICE: codspeed is enabled, but no performance measurement"
                " will be made since it's running in an unknown environment."
                "\033[0m"
            )
        return config, warnings

    def measure(
        self,
        name: str,
        uri: str,
        fn: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        self.benchmark_count += 1
        if self.lib is None:  # Thus should_measure is False
            return fn(*args, **kwargs)

        def __codspeed_root_frame__() -> T:
            return fn(*args, **kwargs)

        if SUPPORTS_PERF_TRAMPOLINE:
            # Warmup CPython performance map cache
            __codspeed_root_frame__()

        self.lib.zero_stats()
        self.lib.start_instrumentation()
        try:
            return __codspeed_root_frame__()
        finally:
            # Ensure instrumentation is stopped even if the test failed
            self.lib.stop_instrumentation()
            self.lib.dump_stats_at(uri.encode("ascii"))

    def report(self, session: Session) -> None:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        count_suffix = "benchmarked" if self.should_measure else "benchmark tested"
        reporter.write_sep(
            "=",
            f"{self.benchmark_count} {count_suffix}",
        )
