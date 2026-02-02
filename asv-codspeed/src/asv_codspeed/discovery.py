from __future__ import annotations

import importlib
import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ASV benchmark name patterns
TIME_PATTERN = re.compile(r"^(Time[A-Z_].+)|(time_.+)$")
TRACK_PATTERN = re.compile(r"^(Track[A-Z_].+)|(track_.+)$")
MEM_PATTERN = re.compile(r"^(Mem[A-Z_].+)|(mem_.+)$")
PEAKMEM_PATTERN = re.compile(r"^(PeakMem[A-Z_].+)|(peakmem_.+)$")
TIMERAW_PATTERN = re.compile(r"^(Timeraw[A-Z_].+)|(timeraw_.+)$")

# Method-level patterns (for class methods)
TIME_METHOD = re.compile(r"^time_")
TRACK_METHOD = re.compile(r"^track_")
MEM_METHOD = re.compile(r"^mem_")
PEAKMEM_METHOD = re.compile(r"^peakmem_")
TIMERAW_METHOD = re.compile(r"^timeraw_")


@dataclass
class ASVBenchmark:
    """Represents a single ASV benchmark to run."""

    name: str
    func: Callable
    type: str  # "time", "track", "mem", "peakmem", "timeraw"
    setup: Callable | None = None
    teardown: Callable | None = None
    params: list[list[Any]] = field(default_factory=list)
    param_names: list[str] = field(default_factory=list)
    current_param_values: tuple[Any, ...] = field(default_factory=tuple)
    timeout: float = 60.0


def _get_benchmark_type_from_name(name: str) -> str | None:
    """Determine benchmark type from function/class name."""
    if TIMERAW_PATTERN.match(name):
        return "timeraw"
    if TIME_PATTERN.match(name):
        return "time"
    if TRACK_PATTERN.match(name):
        return "track"
    if MEM_PATTERN.match(name):
        return "mem"
    if PEAKMEM_PATTERN.match(name):
        return "peakmem"
    return None


def _get_method_type(method_name: str) -> str | None:
    """Determine benchmark type from method name."""
    if TIMERAW_METHOD.match(method_name):
        return "timeraw"
    if TIME_METHOD.match(method_name):
        return "time"
    if TRACK_METHOD.match(method_name):
        return "track"
    if MEM_METHOD.match(method_name):
        return "mem"
    if PEAKMEM_METHOD.match(method_name):
        return "peakmem"
    return None


def _import_module_from_path(module_name: str, file_path: Path):
    """Import a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        del sys.modules[module_name]
        return None
    return module


def _discover_from_module(
    module, module_name: str
) -> list[ASVBenchmark]:
    """Discover benchmarks from a single module."""
    benchmarks = []

    for attr_name in dir(module):
        if attr_name.startswith("_"):
            continue

        attr = getattr(module, attr_name, None)
        if attr is None:
            continue

        # Check if it's a benchmark class
        if isinstance(attr, type):
            btype = _get_benchmark_type_from_name(attr_name)
            if btype is not None:
                # Class-level benchmark: all methods matching the type
                benchmarks.extend(
                    _discover_from_class(attr, f"{module_name}.{attr_name}", btype)
                )
            else:
                # Check individual methods
                benchmarks.extend(
                    _discover_from_class(attr, f"{module_name}.{attr_name}", None)
                )

        # Check if it's a benchmark function
        elif callable(attr):
            btype = _get_method_type(attr_name)
            if btype is not None:
                bench = _create_benchmark(
                    name=f"{module_name}.{attr_name}",
                    func=attr,
                    btype=btype,
                    source=module,
                )
                benchmarks.append(bench)

    return benchmarks


def _discover_from_class(
    cls, class_full_name: str, class_btype: str | None
) -> list[ASVBenchmark]:
    """Discover benchmarks from a class."""
    benchmarks = []
    instance = None

    # Get class-level params
    params = getattr(cls, "params", [])
    param_names = getattr(cls, "param_names", [])
    timeout = getattr(cls, "timeout", 60.0)

    for attr_name in dir(cls):
        if attr_name.startswith("_"):
            continue

        btype = _get_method_type(attr_name)
        if btype is None:
            continue

        # Lazy-instantiate the class
        if instance is None:
            try:
                instance = cls()
            except Exception:
                break

        method = getattr(instance, attr_name, None)
        if method is None or not callable(method):
            continue

        setup_method = getattr(instance, "setup", None)
        teardown_method = getattr(instance, "teardown", None)

        bench_name = f"{class_full_name}.{attr_name}"

        if params:
            # Expand parameterized benchmarks
            param_combos = _expand_params(params)
            for i, combo in enumerate(param_combos):
                param_suffix = _format_param_suffix(combo, param_names)
                benchmarks.append(
                    ASVBenchmark(
                        name=f"{bench_name}({param_suffix})",
                        func=method,
                        type=btype,
                        setup=setup_method,
                        teardown=teardown_method,
                        params=params if isinstance(params[0], list) else [params],
                        param_names=param_names,
                        current_param_values=combo,
                        timeout=timeout,
                    )
                )
        else:
            benchmarks.append(
                ASVBenchmark(
                    name=bench_name,
                    func=method,
                    type=btype,
                    setup=setup_method,
                    teardown=teardown_method,
                    timeout=timeout,
                )
            )

    return benchmarks


def _create_benchmark(
    name: str, func: Callable, btype: str, source: Any
) -> ASVBenchmark:
    """Create a benchmark from a function, inheriting attributes from its source."""
    setup = getattr(source, "setup", None)
    teardown = getattr(source, "teardown", None)
    params = getattr(func, "params", getattr(source, "params", []))
    param_names = getattr(func, "param_names", getattr(source, "param_names", []))
    timeout = getattr(func, "timeout", getattr(source, "timeout", 60.0))

    if params:
        # For now, create one benchmark per param combo
        benchmarks = []
        param_combos = _expand_params(params)
        if len(param_combos) == 1:
            return ASVBenchmark(
                name=f"{name}({_format_param_suffix(param_combos[0], param_names)})",
                func=func,
                type=btype,
                setup=setup,
                teardown=teardown,
                params=params if isinstance(params[0], list) else [params],
                param_names=param_names,
                current_param_values=param_combos[0],
                timeout=timeout,
            )
        # Return first for now - parameterized will be expanded in discover_benchmarks
        return ASVBenchmark(
            name=name,
            func=func,
            type=btype,
            setup=setup,
            teardown=teardown,
            params=params if isinstance(params[0], list) else [params],
            param_names=param_names,
            timeout=timeout,
        )

    return ASVBenchmark(
        name=name,
        func=func,
        type=btype,
        setup=setup,
        teardown=teardown,
        timeout=timeout,
    )


def _expand_params(params: list) -> list[tuple]:
    """Expand parameter lists into all combinations."""
    if not params:
        return [()]

    # If params is a list of lists, compute cartesian product
    if isinstance(params[0], (list, tuple)):
        import itertools

        return list(itertools.product(*params))
    else:
        # Single parameter list
        return [(p,) for p in params]


def _format_param_suffix(values: tuple, names: list[str]) -> str:
    """Format parameter values into a suffix string."""
    parts = []
    for i, v in enumerate(values):
        if i < len(names) and names[i]:
            parts.append(f"{v}")
        else:
            parts.append(f"{v}")
    return ", ".join(parts)


def _discover_benchmark_files(benchmark_dir: Path) -> list[Path]:
    """Find all Python files in the benchmark directory."""
    files = []
    for py_file in sorted(benchmark_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        files.append(py_file)
    return files


def discover_benchmarks(
    benchmark_dir: Path,
    filter_pattern: str | None = None,
) -> list[ASVBenchmark]:
    """Discover all ASV benchmarks in the given directory.

    Args:
        benchmark_dir: Path to the benchmark directory
        filter_pattern: Optional regex to filter benchmark names

    Returns:
        List of discovered benchmarks
    """
    if not benchmark_dir.exists():
        return []

    # Add benchmark dir to sys.path for imports
    benchmark_dir_str = str(benchmark_dir.resolve())
    if benchmark_dir_str not in sys.path:
        sys.path.insert(0, benchmark_dir_str)

    benchmarks: list[ASVBenchmark] = []

    for py_file in _discover_benchmark_files(benchmark_dir):
        # Build module name from relative path
        rel_path = py_file.relative_to(benchmark_dir)
        module_parts = list(rel_path.parts)
        module_parts[-1] = module_parts[-1].removesuffix(".py")
        module_name = ".".join(module_parts)

        module = _import_module_from_path(module_name, py_file)
        if module is None:
            continue

        benchmarks.extend(_discover_from_module(module, module_name))

    # Expand parameterized benchmarks that haven't been expanded yet
    expanded = []
    for bench in benchmarks:
        if bench.params and not bench.current_param_values:
            param_combos = _expand_params(bench.params)
            for combo in param_combos:
                param_suffix = _format_param_suffix(combo, bench.param_names)
                expanded.append(
                    ASVBenchmark(
                        name=f"{bench.name}({param_suffix})",
                        func=bench.func,
                        type=bench.type,
                        setup=bench.setup,
                        teardown=bench.teardown,
                        params=bench.params,
                        param_names=bench.param_names,
                        current_param_values=combo,
                        timeout=bench.timeout,
                    )
                )
        else:
            expanded.append(bench)

    # Apply filter
    if filter_pattern:
        pattern = re.compile(filter_pattern)
        expanded = [b for b in expanded if pattern.search(b.name)]

    return expanded
