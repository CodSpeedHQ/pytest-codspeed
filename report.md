# Segfault in `instrument_hooks_deinit` during Python shutdown

## Issue

CI job `tests (valgrind, 3.13, >=8.1.1)` crashes with exit code 139 (SIGSEGV) after all tests pass.
The segfault occurs during Python's shutdown/GC phase, not during test execution.

Failing CI run: https://github.com/CodSpeedHQ/pytest-codspeed/actions/runs/23649460934/job/68890119732

## Root cause (suspected)

`InstrumentHooks.__del__` calls `instrument_hooks_deinit()` via cffi during Python shutdown.
When multiple `InstrumentHooks` instances are created (e.g. the xdist test loops 5 times, each creating a new instance), their destructors fire during GC at exit and crash — likely because the native library or cffi runtime is already partially torn down.

## Stack trace (from CI)

```
Fatal Python error: Segmentation fault
  File "plugin.py", line 148 in pytest_configure
  ...
  File "test_pytest_plugin_cpu_instrumentation.py", line 116 in test_pytest_xdist_concurrency_compatibility
```

## Minimal repro

```python
# repro.py
import os
os.environ["CODSPEED_ENV"] = "1"

from pytest_codspeed.instruments.hooks import InstrumentHooks

for i in range(5):
    h = InstrumentHooks()
    print(f"Created instance {i}: {h.instance}")

del h
print("Exiting...")
```

```
uv run python repro.py
# Segfaults at exit with code 139
```

## Key files

- `src/pytest_codspeed/instruments/hooks/__init__.py` — `InstrumentHooks.__del__` calls `instrument_hooks_deinit`
- `src/pytest_codspeed/instruments/hooks/build.py` — cffi bindings for the native library
- `src/pytest_codspeed/instruments/analysis.py` — creates `InstrumentHooks` in `__init__`
- `tests/test_pytest_plugin_cpu_instrumentation.py::test_pytest_xdist_concurrency_compatibility` — triggers the bug by creating 5 successive instances
