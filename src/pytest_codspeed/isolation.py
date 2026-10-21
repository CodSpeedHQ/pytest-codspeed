"""Process isolation: every benchmark runs in a fresh pytest process, so the
allocator state, caches and threads that other benchmarks or setup code leave
behind can't change its measurement."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence

# Isolation is on unless this is `0` or `false`.
PROCESS_ISOLATION_ENV = "CODSPEED_PROCESS_ISOLATION"
# Set on each child process: the URI of the only benchmark it runs.
ISOLATED_BENCHMARK_ENV = "CODSPEED_ISOLATED_BENCHMARK"

ENABLED_VALUES = ("1", "true")
DISABLED_VALUES = ("0", "false")

# Shells report a child killed by signal N as exit code 128 + N.
SIGNAL_EXIT_CODE_OFFSET = 128

# The parent already printed the session header and summary, so children only
# print what is needed to debug a failure.
CHILD_PYTEST_ARGS = ("-q",)


class IsolationKind(Enum):
    # All benchmarks share this process and its allocator state.
    SHARED_PROCESS = "shared-process"
    # Every benchmark runs in its own child process.
    PROCESS_PER_BENCHMARK = "process-per-benchmark"
    # A child spawned by PROCESS_PER_BENCHMARK, restricted to one URI.
    ISOLATED_BENCHMARK = "isolated-benchmark"


@dataclass(frozen=True)
class Isolation:
    """How the plugin runs each benchmark."""

    kind: IsolationKind
    # Only set for ISOLATED_BENCHMARK.
    uri: str | None = None

    @staticmethod
    def current() -> Isolation:
        """The isolation of this process, read from the environment. The plugin
        calls it once per pytest session; no process-wide cache, so in-process
        runs (`pytester`) can use different settings."""
        uri = os.environ.get(ISOLATED_BENCHMARK_ENV)
        if uri is not None:
            return Isolation(IsolationKind.ISOLATED_BENCHMARK, uri)

        value = os.environ.get(PROCESS_ISOLATION_ENV)
        if value is None or value in ENABLED_VALUES:
            return Isolation(IsolationKind.PROCESS_PER_BENCHMARK)
        if value in DISABLED_VALUES:
            return Isolation(IsolationKind.SHARED_PROCESS)
        raise ValueError(
            f"{PROCESS_ISOLATION_ENV} must be `true` or `false`, got `{value}`"
        )

    def only_benchmark(self) -> str | None:
        """The only benchmark this process may run. It overrides CLI filters."""
        if self.kind is IsolationKind.ISOLATED_BENCHMARK:
            return self.uri
        return None


def run_in_child_process(uri: str, args: Sequence[str], cwd: Path) -> int:
    """Runs pytest again with the same arguments, limited to `uri`, and returns
    the exit code of the child in the shell convention."""
    # Keep the parent's output before the child's.
    sys.stdout.flush()
    sys.stderr.flush()

    # `sys.orig_argv` only exists on Python 3.10+, and pytest can run in-process
    # (e.g. `pytest.main`), so rebuild the command from pytest's own arguments.
    command = [sys.executable, "-m", "pytest", *args, *CHILD_PYTEST_ARGS]
    env = {**os.environ, ISOLATED_BENCHMARK_ENV: uri}
    returncode = subprocess.run(command, cwd=cwd, env=env).returncode
    if returncode < 0:
        return SIGNAL_EXIT_CODE_OFFSET - returncode
    return returncode
