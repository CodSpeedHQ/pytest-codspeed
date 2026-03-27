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
    from cffi import FFI

    from .dist_instrument_hooks import InstrumentHooksPointer, LibType

# Feature flags for instrument hooks
FEATURE_DISABLE_CALLGRIND_MARKERS = 0


class InstrumentHooks:
    """Zig library wrapper class providing benchmark measurement functionality."""

    lib: LibType
    ffi: FFI
    instance: InstrumentHooksPointer

    def __init__(self) -> None:
        if os.environ.get("CODSPEED_ENV") is None:
            raise RuntimeError(
                "Can't run benchmarks outside of CodSpeed environment."
                "Please set the CODSPEED_ENV environment variable."
            )

        try:
            from .dist_instrument_hooks import ffi, lib  # type: ignore
        except ImportError as e:
            raise RuntimeError(f"Failed to load instrument hooks library: {e}") from e
        self.lib = lib
        self.ffi = ffi

        self.instance = self.lib.instrument_hooks_init()
        if self.instance == 0:
            raise RuntimeError("Failed to initialize CodSpeed instrumentation library.")

        if SUPPORTS_PERF_TRAMPOLINE and not sys.is_stack_trampoline_active():
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

        ret = self.lib.instrument_hooks_set_executed_benchmark(
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
        """Check if simulation is active."""
        return self.lib.instrument_hooks_is_instrumented(self.instance)

    def set_feature(self, feature: int, enabled: bool) -> None:
        """Set a feature flag in the instrument hooks library.

        Args:
            feature: The feature flag to set
            enabled: Whether to enable or disable the feature
        """
        self.lib.instrument_hooks_set_feature(feature, enabled)

    def set_environment(self, section_name: str, key: str, value: str) -> None:
        """Register a key-value pair under a named section for environment collection.

        Args:
            section_name: The section name (e.g. "Python")
            key: The key (e.g. "version")
            value: The value (e.g. "3.13.12")
        """
        ret = self.lib.instrument_hooks_set_environment(
            self.instance,
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
        encoded = [self.ffi.new("char[]", v.encode("utf-8")) for v in values]
        c_values = self.ffi.new("char*[]", encoded)
        ret = self.lib.instrument_hooks_set_environment_list(
            self.instance,
            section_name.encode("utf-8"),
            key.encode("utf-8"),
            c_values,
            len(encoded),
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
        ret = self.lib.instrument_hooks_write_environment(self.instance, pid)
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
