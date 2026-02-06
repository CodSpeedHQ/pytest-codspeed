from __future__ import annotations

import os
import sys
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

from pytest_codspeed.utils import SUPPORTS_PERF_TRAMPOLINE


class InstrumentHooks:
    """Native library wrapper class providing benchmark measurement functionality."""

    _module: Any
    _instance: Any

    def __init__(self) -> None:
        if os.environ.get("CODSPEED_ENV") is None:
            raise RuntimeError(
                "Can't run benchmarks outside of CodSpeed environment."
                "Please set the CODSPEED_ENV environment variable."
            )

        try:
            from . import dist_instrument_hooks  # type: ignore
        except ImportError as e:
            raise RuntimeError(f"Failed to load instrument hooks library: {e}") from e
        self._module = dist_instrument_hooks

        self._instance = self._module.instrument_hooks_init()
        if self._instance is None:
            raise RuntimeError("Failed to initialize CodSpeed instrumentation library.")

        if SUPPORTS_PERF_TRAMPOLINE:
            sys.activate_stack_trampoline("perf")  # type: ignore

    def __del__(self):
        # Don't manually deinit - let the capsule destructor handle it
        pass

    def start_benchmark(self) -> None:
        """Start a new benchmark measurement."""
        ret = self._module.instrument_hooks_start_benchmark(self._instance)
        if ret != 0:
            warnings.warn("Failed to start benchmark measurement", RuntimeWarning)

    def stop_benchmark(self) -> None:
        """Stop the current benchmark measurement."""
        ret = self._module.instrument_hooks_stop_benchmark(self._instance)
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

        ret = self._module.instrument_hooks_set_executed_benchmark(
            self._instance, pid, uri.encode("ascii")
        )
        if ret != 0:
            warnings.warn("Failed to set executed benchmark", RuntimeWarning)

    def set_integration(self, name: str, version: str) -> None:
        """Set the integration name and version."""
        ret = self._module.instrument_hooks_set_integration(
            self._instance, name.encode("ascii"), version.encode("ascii")
        )
        if ret != 0:
            warnings.warn("Failed to set integration name and version", RuntimeWarning)

    def is_instrumented(self) -> bool:
        """Check if simulation is active."""
        return self._module.instrument_hooks_is_instrumented(self._instance)

    def callgrind_start_instrumentation(self) -> None:
        """Start callgrind instrumentation."""
        self._module.callgrind_start_instrumentation()

    def callgrind_stop_instrumentation(self) -> None:
        """Stop callgrind instrumentation."""
        self._module.callgrind_stop_instrumentation()
