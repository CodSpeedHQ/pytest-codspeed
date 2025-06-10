from __future__ import annotations

import os
import sys
import warnings
from typing import TYPE_CHECKING

from pytest_codspeed.utils import SUPPORTS_PERF_TRAMPOLINE

if TYPE_CHECKING:
    from .dist_instrument_hooks import InstrumentHooksPointer, LibType


class InstrumentHooks:
    """Zig library wrapper class providing benchmark measurement functionality."""

    lib: LibType
    instance: InstrumentHooksPointer

    def __init__(self) -> None:
        if os.environ.get("CODSPEED_ENV") is None:
            raise RuntimeError(
                "Can't run benchmarks outside of CodSpeed environment."
                "Please set the CODSPEED_ENV environment variable."
            )

        try:
            from .dist_instrument_hooks import lib  # type: ignore
        except ImportError as e:
            raise RuntimeError(f"Failed to load instrument hooks library: {e}") from e
        self.lib = lib

        self.instance = self.lib.instrument_hooks_init()
        if self.instance == 0:
            raise RuntimeError("Failed to initialize CodSpeed instrumentation library.")

        if SUPPORTS_PERF_TRAMPOLINE:
            sys.activate_stack_trampoline("perf")  # type: ignore

    def __del__(self):
        if hasattr(self, "lib") and hasattr(self, "instance"):
            self.lib.instrument_hooks_deinit(self.instance)

    def start_benchmark(self) -> None:
        """Start a new benchmark measurement."""
        ret = self.lib.instrument_hooks_start_benchmark(self.instance)
        if ret != 0:
            warnings.warn("Failed to start benchmark measurement", RuntimeWarning)

    def stop_benchmark(self) -> None:
        """Stop the current benchmark measurement."""
        ret = self.lib.instrument_hooks_stop_benchmark(self.instance)
        if ret != 0:
            warnings.warn("Failed to stop benchmark measurement", RuntimeWarning)

    def set_executed_benchmark(self, uri: str, pid: int | None = None) -> None:
        """Set the executed benchmark URI and process ID.

        Args:
            uri: The benchmark URI string identifier
            pid: Optional process ID (defaults to current process)
        """
        if pid is None:
            pid = os.getpid()

        ret = self.lib.instrument_hooks_executed_benchmark(
            self.instance, pid, uri.encode("ascii")
        )
        if ret != 0:
            warnings.warn("Failed to set executed benchmark", RuntimeWarning)

    def set_integration(self, name: str, version: str) -> None:
        """Set the integration name and version."""
        ret = self.lib.instrument_hooks_set_integration(
            self.instance, name.encode("ascii"), version.encode("ascii")
        )
        if ret != 0:
            warnings.warn("Failed to set integration name and version", RuntimeWarning)

    def is_instrumented(self) -> bool:
        """Check if instrumentation is active."""
        return self.lib.instrument_hooks_is_instrumented(self.instance)
