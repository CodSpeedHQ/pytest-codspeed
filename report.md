# Segfault in instrument hooks during Python shutdown

## Issue

CI job `tests (valgrind, 3.13, >=8.1.1)` crashes with exit code 139 (SIGSEGV) after all tests pass.

Failing CI run: https://github.com/CodSpeedHQ/pytest-codspeed/actions/runs/23649460934/job/68890119732

## Root cause

Calling `sys.activate_stack_trampoline("perf")` multiple times after loading a cffi native library causes a segfault at process exit on CPython 3.13.12 (works fine on 3.13.11). This is a CPython regression.

`InstrumentHooks.__init__` unconditionally calls `sys.activate_stack_trampoline("perf")`. When multiple instances are created (e.g. the xdist test loops 5 times inprocess), the repeated activation triggers the crash.

## Fix

Guard the trampoline activation with `sys.is_stack_trampoline_active()` in `InstrumentHooks.__init__`:

```python
if SUPPORTS_PERF_TRAMPOLINE and not sys.is_stack_trampoline_active():
    sys.activate_stack_trampoline("perf")
```

## Verification

- `uv run --python 3.13.12 python repro.py` → exit 0 (was exit 139)
- `test_pytest_xdist_concurrency_compatibility` → PASSED, exit 0 (was exit 139)
