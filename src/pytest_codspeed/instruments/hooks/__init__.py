from __future__ import annotations

import os
import platform
import shlex
import sys
import sysconfig
import warnings
from typing import TYPE_CHECKING

from pytest_codspeed.utils import SUPPORTS_PERF_TRAMPOLINE

if TYPE_CHECKING:
    from typing import Any, Callable


class InstrumentHooks:
    """Native library wrapper class providing benchmark measurement functionality."""

    _module: Any
    _instance: Any
    # Bound directly to the C functions in __init__ to avoid an extra Python
    # stack frame when starting/stopping callgrind instrumentation.
    callgrind_start_instrumentation: Callable[[], None]
    callgrind_stop_instrumentation: Callable[[], None]

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
        self.callgrind_start_instrumentation = (
            dist_instrument_hooks.callgrind_start_instrumentation
        )
        self.callgrind_stop_instrumentation = (
            dist_instrument_hooks.callgrind_stop_instrumentation
        )

        self._instance = self._module.instrument_hooks_init()
        if self._instance is None:
            raise RuntimeError("Failed to initialize CodSpeed instrumentation library.")

        if SUPPORTS_PERF_TRAMPOLINE and not sys.is_stack_trampoline_active():
            sys.activate_stack_trampoline("perf")  # type: ignore

        # Ignore libpython and python executable frames in callgrind so they
        # don't obfuscate the flamegraph.
        self._callgrind_skip_python_runtime()

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

    @staticmethod
    def current_timestamp() -> int:
        """Return a monotonic timestamp in nanoseconds from the native library."""
        from . import dist_instrument_hooks  # type: ignore

        return dist_instrument_hooks.instrument_hooks_current_timestamp()

    def add_marker(
        self, marker_type: int, timestamp: int, pid: int | None = None
    ) -> None:
        """Emit a single marker at the given timestamp."""
        if pid is None:
            pid = os.getpid()
        ret = self._module.instrument_hooks_add_marker(
            self._instance, pid, marker_type, timestamp
        )
        if ret != 0:
            warnings.warn("Failed to add marker", RuntimeWarning)

    def add_benchmark_timestamps(self, start: int, end: int) -> None:
        """Emit a BenchmarkStart/BenchmarkEnd marker pair around a captured window."""
        self.add_marker(self._module.MARKER_TYPE_BENCHMARK_START, start)
        self.add_marker(self._module.MARKER_TYPE_BENCHMARK_END, end)

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

    def _set_feature(self, feature: int, enabled: bool) -> None:
        """Set a feature flag in the instrument hooks library.

        Args:
            feature: The feature flag to set
            enabled: Whether to enable or disable the feature
        """
        self._module.instrument_hooks_set_feature(feature, enabled)

    def disable_callgrind_markers(self, disabled: bool = True) -> None:
        """Disable automatic callgrind markers around benchmark start/stop."""
        self._set_feature(self._module.FEATURE_DISABLE_CALLGRIND_MARKERS, disabled)

    def set_environment(self, section_name: str, key: str, value: str) -> None:
        """Register a key-value pair under a named section for environment collection.

        Args:
            section_name: The section name (e.g. "Python")
            key: The key (e.g. "version")
            value: The value (e.g. "3.13.12")
        """
        ret = self._module.instrument_hooks_set_environment(
            self._instance,
            section_name.encode("utf-8"),
            key.encode("utf-8"),
            value.encode("utf-8"),
        )
        if ret != 0:
            warnings.warn("Failed to set environment data", RuntimeWarning)

    def set_environment_list(
        self, section_name: str, key: str, values: list[str]
    ) -> None:
        """Register a list of values under a named section for environment collection.

        Args:
            section_name: The section name (e.g. "python")
            key: The key (e.g. "build_args")
            values: The list of string values
        """
        ret = self._module.instrument_hooks_set_environment_list(
            self._instance,
            section_name.encode("utf-8"),
            key.encode("utf-8"),
            [v.encode("utf-8") for v in values],
        )
        if ret != 0:
            warnings.warn("Failed to set environment list data", RuntimeWarning)

    def write_environment(self, pid: int | None = None) -> None:
        """Flush all registered environment sections to disk.

        Writes to $CODSPEED_PROFILE_FOLDER/environment-<pid>.json.

        Args:
            pid: Optional process ID (defaults to current process)
        """
        if pid is None:
            pid = os.getpid()
        ret = self._module.instrument_hooks_write_environment(self._instance, pid)
        if ret != 0:
            warnings.warn("Failed to write environment data", RuntimeWarning)

    def collect_and_write_python_environment(self) -> None:
        """Collect Python toolchain information and write it to disk."""
        section = "python"
        set_env = self.set_environment

        # Core identity
        set_env(section, "version", sys.version.strip())
        set_env(section, "implementation", sys.implementation.name.strip())
        set_env(section, "compiler", platform.python_compiler().strip())

        config_vars = sysconfig.get_config_vars()

        # Build arguments as a list
        config_args = config_vars.get("CONFIG_ARGS", "")
        if config_args:
            build_args = [arg.strip() for arg in shlex.split(config_args)]
            self.set_environment_list(section, "build_args", build_args)

        # Performance-relevant build configuration as "KEY=value" list
        _SYSCONFIG_KEYS = (
            "abiflags",
            "PY_ENABLE_SHARED",
            "Py_GIL_DISABLED",
            "Py_DEBUG",
            "WITH_PYMALLOC",
            "WITH_MIMALLOC",
            "WITH_FREELISTS",
            "HAVE_COMPUTED_GOTOS",
            "Py_STATS",
            "Py_TRACE_REFS",
            "WITH_VALGRIND",
            "WITH_DTRACE",
        )
        config_items = []
        for key in _SYSCONFIG_KEYS:
            value = config_vars.get(key)
            if value is not None:
                config_items.append(f"{key}={str(value).strip()}")
        config_items.append(f"perf_trampoline={SUPPORTS_PERF_TRAMPOLINE}")
        self.set_environment_list(section, "config", config_items)

        self.write_environment()

    def _callgrind_skip_python_runtime(self) -> None:
        """Skip libpython and the python executable from callgrind measurement."""
        ldlibrary = sysconfig.get_config_var("LDLIBRARY")
        libdir = sysconfig.get_config_var("LIBDIR")
        libpython = next(
            (
                p
                for p in (
                    os.path.join(libdir, ldlibrary) if ldlibrary and libdir else None,
                    os.path.join(sys.prefix, "lib", ldlibrary) if ldlibrary else None,
                )
                if p and os.path.exists(p)
            ),
            None,
        )
        if libpython:
            self._module.callgrind_add_obj_skip(libpython.encode())
        self._module.callgrind_add_obj_skip(sys.executable.encode())
