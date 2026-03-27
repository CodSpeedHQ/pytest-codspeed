# Segfault at exit when calling `sys.activate_stack_trampoline("perf")` multiple times (regression in 3.13.12)

## Bug report

Calling `sys.activate_stack_trampoline("perf")` 3+ times in a process that has loaded a native library via `ctypes.CDLL` (or cffi) causes a segfault during interpreter shutdown on CPython 3.13.12. This worked fine on 3.13.11.

This is likely a regression introduced by the fix for #143228 (reference counting for perf trampolines).

## Minimal reproduction

```python
import sys, ctypes
ctypes.CDLL(None)
sys.activate_stack_trampoline("perf")
sys.activate_stack_trampoline("perf")
sys.activate_stack_trampoline("perf")
```

```
$ python3.13 --version
Python 3.13.12
$ python3.13 repro.py
Segmentation fault (core dumped)    # exit code 139
```

100% reproducible on 3.13.12, exits cleanly on 3.13.11.

### Notes

- The crash occurs during interpreter finalization, not at the point of the call
- No exception is raised; `is_stack_trampoline_active()` returns `True` after each call
- Without `ctypes.CDLL`, 3 calls don't crash (but 10 calls do crash with "no more code watcher IDs available" + segfault)
- 2 calls + `ctypes.CDLL` doesn't crash; 3 calls is the threshold

## Expected behavior

Repeated calls to `activate_stack_trampoline("perf")` when the trampoline is already active should either be a no-op or raise an error — not cause a segfault at shutdown.

## Workaround

Guard with `is_stack_trampoline_active()`:

```python
if not sys.is_stack_trampoline_active():
    sys.activate_stack_trampoline("perf")
```

## Affected versions

| Python | Result |
|--------|--------|
| 3.13.11 | exit 0 |
| 3.13.12 | **exit 139 (segfault)** |
| 3.14.2 | exit 0 |
| 3.14.3 | **exit 139 (segfault)** |

The regression was introduced in both 3.13.12 and 3.14.3, likely via the backport of the fix for #143228.

## Environment

- Linux x86_64 (6.12.76)
